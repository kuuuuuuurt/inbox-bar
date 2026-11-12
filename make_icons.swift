// Renders icons/{light,dark}/N.png: the menu bar tray with a red count badge on its corner.
// light = black tray for a light menu bar, dark = white tray. Run from this folder: swift make_icons.swift
import AppKit
let red = NSColor(srgbRed: 1, green: 0.23, blue: 0.19, alpha: 1)
func rounded(_ size: CGFloat) -> NSFont {
    let f = NSFont.systemFont(ofSize: size, weight: .bold)
    return NSFont(descriptor: f.fontDescriptor.withDesign(.rounded)!, size: size)!
}
func render(_ text: String, tray: NSColor, to path: String) {
    let s = NSAttributedString(string: text, attributes: [.font: rounded(9.5), .foregroundColor: NSColor.white])
    let bw = max(13, s.size().width + 6), h: CGFloat = 22
    let w = 13 + bw
    let img = NSImage(size: NSSize(width: w, height: h))
    img.lockFocus()
    let cfg = NSImage.SymbolConfiguration(pointSize: 15, weight: .regular).applying(.init(paletteColors: [tray]))
    NSImage(systemSymbolName: "tray", accessibilityDescription: nil)!.withSymbolConfiguration(cfg)!
        .draw(in: NSRect(x: 0, y: 2, width: 20, height: 15))
    red.setFill()
    NSBezierPath(roundedRect: NSRect(x: 13, y: 10, width: bw, height: 12), xRadius: 6, yRadius: 6).fill()
    s.draw(at: NSPoint(x: 13 + (bw - s.size().width) / 2, y: 10 + (12 - s.size().height) / 2))
    img.unlockFocus()
    // 2x bitmap so it's sharp on Retina
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: Int(w * 2), pixelsHigh: Int(h * 2), bitsPerSample: 8,
                               samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    rep.size = img.size
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    img.draw(in: NSRect(origin: .zero, size: img.size))
    NSGraphicsContext.restoreGraphicsState()
    try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: path))
}
for (mode, color) in [("light", NSColor.black), ("dark", NSColor.white)] {
    try! FileManager.default.createDirectory(atPath: "icons/\(mode)", withIntermediateDirectories: true)
    for n in 1...99 { render(String(n), tray: color, to: "icons/\(mode)/\(n).png") }
    render("99+", tray: color, to: "icons/\(mode)/99+.png")
    render("•", tray: color, to: "icons/\(mode)/dot.png")
}

// Dropdown row icons: icons/rows/<name>-<on|off>.png (SwiftBar's own colored symbols vanish after hover).
func hex(_ h: Int) -> NSColor { NSColor(srgbRed: CGFloat(h >> 16 & 255) / 255, green: CGFloat(h >> 8 & 255) / 255, blue: CGFloat(h & 255) / 255, alpha: 1) }
try! FileManager.default.createDirectory(atPath: "icons/rows", withIntermediateDirectories: true)
for (name, symbol, color) in [("gmail", "envelope.fill", 0xEA4335), ("slack", "number.square.fill", 0xE01E5A),
                              ("chat", "bubble.left.and.bubble.right.fill", 0x34A853)] {
    for (state, c) in [("on", hex(color)), ("off", hex(0x8E8E93))] {
        let cfg = NSImage.SymbolConfiguration(pointSize: 13, weight: .regular).applying(.init(paletteColors: [c]))
        let sym = NSImage(systemSymbolName: symbol, accessibilityDescription: nil)!.withSymbolConfiguration(cfg)!
        let size = NSSize(width: 18, height: 16)
        let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 36, pixelsHigh: 32, bitsPerSample: 8, samplesPerPixel: 4,
                                   hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
        rep.size = size
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
        let s = sym.size
        sym.draw(in: NSRect(x: (size.width - s.width) / 2, y: (size.height - s.height) / 2, width: s.width, height: s.height))
        NSGraphicsContext.restoreGraphicsState()
        try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: "icons/rows/\(name)-\(state).png"))
    }
}
