# encoding: utf-8

###########################################################################################################
#
#  Snippet Palette
#  A Glyphs 3 Palette Plugin for running small scripts from buttons in the sidebar.
#
#  - 4 buttons (2x2 grid) in the sidebar palette
#  - Each button can have a title and a script
#  - Option+click or right-click a button to configure it
#  - Hover to see the title as tooltip
#  - Settings persist across all Glyphs files via Glyphs.defaults
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
import objc
import json
import traceback
import GlyphsApp
from GlyphsApp import Glyphs
from GlyphsApp.plugins import PalettePlugin

from AppKit import (
	NSButton,
	NSBezelStyleSmallSquare,
	NSView,
	NSMakeRect,
	NSFont,
	NSAlternateKeyMask,
)

# Try to import vanilla; if not available, we'll handle it gracefully
try:
	from vanilla import Window, Group, TextEditor, EditText, Button as VanillaButton, TextBox
	HAS_VANILLA = True
except ImportError:
	HAS_VANILLA = False


DEFAULTS_KEY = "com.toktaro.SnippetPalette.snippets"
BUTTON_COUNT = 4
PALETTE_HEIGHT = 80
BUTTON_PADDING = 6
BUTTON_GAP = 6
MAX_CONTENT_WIDTH = 300


class SnippetButton(NSButton):
	"""Custom NSButton subclass that detects Option+click and right-click."""

	def initWithFrame_(self, frame):
		self = objc.super(SnippetButton, self).initWithFrame_(frame)
		if self is None:
			return None
		return self

	def mouseDown_(self, event):
		# Option+click → open config
		if event.modifierFlags() & NSAlternateKeyMask:
			if hasattr(self, '_palettePlugin') and self._palettePlugin:
				self._palettePlugin.openConfigForButton_(self._buttonIndex)
				return
		objc.super(SnippetButton, self).mouseDown_(event)

	def rightMouseDown_(self, event):
		# Right-click → open config
		if hasattr(self, '_palettePlugin') and self._palettePlugin:
			self._palettePlugin.openConfigForButton_(self._buttonIndex)
			return
		objc.super(SnippetButton, self).rightMouseDown_(event)


class SnippetPaletteView(NSView):
	"""Custom NSView that lays out 4 buttons in a 2x2 grid,
	   stretching to fill width up to MAX_CONTENT_WIDTH, then centering."""

	def initWithFrame_buttons_padding_gap_maxWidth_(self, frame, buttons, padding, gap, maxWidth):
		self = objc.super(SnippetPaletteView, self).initWithFrame_(frame)
		if self is None:
			return None
		self._buttons = buttons
		self._padding = padding
		self._gap = gap
		self._maxWidth = maxWidth
		for btn in buttons:
			self.addSubview_(btn)
		self._layoutButtons()
		return self

	def resizeSubviewsWithOldSize_(self, oldSize):
		self._layoutButtons()

	def _layoutButtons(self):
		viewW = self.frame().size.width
		viewH = self.frame().size.height
		padding = self._padding
		gap = self._gap

		# Content area: limited by maxWidth, centered if wider
		contentW = min(viewW, self._maxWidth)
		offsetX = (viewW - contentW) / 2.0

		buttonW = (contentW - padding * 2 - gap) / 2.0
		buttonH = (viewH - padding * 2 - gap) / 2.0

		for i, btn in enumerate(self._buttons):
			row = i // 2
			col = i % 2
			x = offsetX + padding + col * (buttonW + gap)
			# NSView: y=0 is bottom, row 0 = top row
			y = viewH - padding - (row + 1) * buttonH - row * gap
			btn.setFrame_(NSMakeRect(x, y, buttonW, buttonH))


class SnippetPalette(PalettePlugin):

	@objc.python_method
	def settings(self):
		self.name = 'Snippet Palette'

		# Load saved snippets
		self.snippets = self._loadSnippets()

		# Build the UI
		self._buildUI()

	@objc.python_method
	def _buildUI(self):
		# Create buttons first
		buttonH = (PALETTE_HEIGHT - BUTTON_PADDING * 2 - BUTTON_GAP) // 2
		btns = []
		for i in range(BUTTON_COUNT):
			btn = SnippetButton.alloc().initWithFrame_(
				NSMakeRect(0, 0, 50, buttonH)
			)
			btn.setBezelStyle_(NSBezelStyleSmallSquare)
			btn.setFont_(NSFont.systemFontOfSize_(11))
			btn._palettePlugin = self
			btn._buttonIndex = i
			btn.setTarget_(self)
			btn.setAction_(objc.selector(self.buttonClicked_, signature=b'v@:@'))
			btn.setTag_(i)
			self._updateButtonAppearance(btn, i)
			btns.append(btn)

		self.buttons = btns

		# Create the custom view that handles responsive layout
		self.paletteView = SnippetPaletteView.alloc().initWithFrame_buttons_padding_gap_maxWidth_(
			NSMakeRect(0, 0, 200, PALETTE_HEIGHT),
			btns,
			BUTTON_PADDING,
			BUTTON_GAP,
			MAX_CONTENT_WIDTH,
		)

		self.dialog = self.paletteView

	@objc.python_method
	def _updateButtonAppearance(self, btn, index):
		"""Update button tooltip based on stored snippet. Label is always the number."""
		snippet = self.snippets.get(str(index), {})
		title = snippet.get('title', '')
		script = snippet.get('script', '')

		# Always show the number as button label
		btn.setTitle_(str(index + 1))

		# Tooltip: title > script preview > default hint
		if title:
			btn.setToolTip_(title)
		elif script:
			btn.setToolTip_(script[:80])
		else:
			btn.setToolTip_('Option+click or right-click to configure')

	@objc.python_method
	def _updateAllButtons(self):
		"""Refresh all button appearances from current snippets data."""
		for i, btn in enumerate(self.buttons):
			self._updateButtonAppearance(btn, i)

	# ---- Snippet storage ----

	@objc.python_method
	def _loadSnippets(self):
		"""Load snippets from Glyphs.defaults."""
		raw = Glyphs.defaults[DEFAULTS_KEY]
		if raw:
			try:
				return json.loads(raw)
			except Exception:
				pass
		return {}

	@objc.python_method
	def _saveSnippets(self):
		"""Save snippets to Glyphs.defaults."""
		Glyphs.defaults[DEFAULTS_KEY] = json.dumps(self.snippets, ensure_ascii=False)

	# ---- Button actions ----

	def buttonClicked_(self, sender):
		"""Normal click: execute the script for this button."""
		index = sender.tag()
		self._executeSnippet(index)

	@objc.python_method
	def _executeSnippet(self, index):
		"""Execute the stored script for the given button index."""
		snippet = self.snippets.get(str(index), {})
		script = snippet.get('script', '')
		if not script:
			# No script configured — open config instead
			self.openConfigForButton_(index)
			return

		try:
			# Build execution context similar to Macro window
			font = Glyphs.font
			exec_globals = {
				'__builtins__': __builtins__,
				'Glyphs': Glyphs,
				'Font': font,
			}
			# Add all GlyphsApp public symbols (GSGuide, GSGlyph, etc.)
			# so scripts run identically to the Macro window
			for _name in dir(GlyphsApp):
				if not _name.startswith('_'):
					exec_globals.setdefault(_name, getattr(GlyphsApp, _name))
			# Add commonly used shortcuts if a font is open
			if font is not None:
				exec_globals['selectedLayers'] = font.selectedLayers
			exec(script, exec_globals)
		except Exception:
			# Log the error to the Macro window
			error_msg = traceback.format_exc()
			print("Snippet Palette — Error in button %d:\n%s" % (index + 1, error_msg))
			Glyphs.showMacroWindow()

	# ---- Configuration dialog ----

	def openConfigForButton_(self, index):
		"""Open a dialog to configure the snippet for the given button index."""
		if not HAS_VANILLA:
			print("Snippet Palette: vanilla library is required. Install it via Glyphs Plugin Manager.")
			return

		snippet = self.snippets.get(str(index), {})
		currentTitle = snippet.get('title', '')
		currentScript = snippet.get('script', '')

		self._configIndex = index

		self._configWindow = Window(
			(400, 320),
			'Configure Button %d' % (index + 1),
			minSize=(300, 250),
		)
		w = self._configWindow

		y = 10
		w.titleLabel = TextBox((10, y, -10, 17), 'Title:', sizeStyle='small')
		y += 20
		w.titleField = EditText((10, y, -10, 22), text=currentTitle, sizeStyle='small')
		y += 32
		w.scriptLabel = TextBox((10, y, -10, 17), 'Script:', sizeStyle='small')
		y += 20
		w.scriptEditor = TextEditor((10, y, -10, -40), text=currentScript)

		w.cancelButton = VanillaButton((-190, -32, 80, 22), 'Cancel', sizeStyle='small', callback=self._configCancel)
		w.saveButton = VanillaButton((-100, -32, 90, 22), 'Save', sizeStyle='small', callback=self._configSave)

		w.open()

	@objc.python_method
	def _configSave(self, sender):
		"""Save the configuration from the dialog."""
		w = self._configWindow
		title = w.titleField.get().strip()
		script = w.scriptEditor.get().strip()

		self.snippets[str(self._configIndex)] = {
			'title': title,
			'script': script,
		}
		self._saveSnippets()
		self._updateAllButtons()

		w.close()
		del self._configWindow

	@objc.python_method
	def _configCancel(self, sender):
		"""Cancel the configuration dialog."""
		self._configWindow.close()
		del self._configWindow

	# ---- Palette sizing ----

	def minHeight(self):
		return PALETTE_HEIGHT

	def maxHeight(self):
		return PALETTE_HEIGHT

	@objc.python_method
	def start(self):
		pass

	@objc.python_method
	def __del__(self):
		pass

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
