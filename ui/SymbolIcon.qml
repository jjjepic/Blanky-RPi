import QtQuick

Canvas {
    id: icon

    property string kind: ""
    property color iconColor: "white"
    property bool muted: false

    implicitWidth: 24
    implicitHeight: 24

    onKindChanged: requestPaint()
    onIconColorChanged: requestPaint()
    onMutedChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        var ctx = getContext("2d")
        ctx.clearRect(0, 0, width, height)
        var size = Math.min(width, height)
        ctx.save()
        ctx.translate(width / 2, height / 2)
        ctx.strokeStyle = iconColor
        ctx.fillStyle = iconColor
        ctx.lineWidth = Math.max(1.6, size * 0.095)
        ctx.lineCap = "round"
        ctx.lineJoin = "round"

        if (kind === "arrow") {
            ctx.lineWidth = Math.max(2, size * 0.14)
            ctx.beginPath()
            ctx.moveTo(-size * 0.12, -size * 0.27)
            ctx.lineTo(size * 0.13, 0)
            ctx.lineTo(-size * 0.12, size * 0.27)
            ctx.stroke()
        } else if (kind === "power") {
            ctx.beginPath()
            ctx.arc(0, size * 0.035, size * 0.32, -Math.PI / 4, Math.PI * 1.25)
            ctx.stroke()
            ctx.beginPath()
            ctx.moveTo(0, -size * 0.42)
            ctx.lineTo(0, -size * 0.04)
            ctx.stroke()
        } else if (kind === "volume") {
            ctx.beginPath()
            ctx.moveTo(-size * 0.40, -size * 0.15)
            ctx.lineTo(-size * 0.23, -size * 0.15)
            ctx.lineTo(-size * 0.06, -size * 0.31)
            ctx.lineTo(-size * 0.06, size * 0.31)
            ctx.lineTo(-size * 0.23, size * 0.15)
            ctx.lineTo(-size * 0.40, size * 0.15)
            ctx.closePath()
            ctx.fill()
            ctx.lineWidth = Math.max(1.4, size * 0.075)
            if (muted) {
                ctx.beginPath()
                ctx.moveTo(size * 0.16, -size * 0.13)
                ctx.lineTo(size * 0.38, size * 0.13)
                ctx.moveTo(size * 0.38, -size * 0.13)
                ctx.lineTo(size * 0.16, size * 0.13)
                ctx.stroke()
            } else {
                ctx.beginPath()
                ctx.arc(-size * 0.06, 0, size * 0.24, -Math.PI / 3, Math.PI / 3)
                ctx.stroke()
                ctx.beginPath()
                ctx.arc(-size * 0.06, 0, size * 0.40, -Math.PI / 3, Math.PI / 3)
                ctx.stroke()
            }
        } else if (kind === "microphone") {
            ctx.beginPath()
            ctx.arc(0, -size * 0.23, size * 0.13, Math.PI, Math.PI * 2)
            ctx.lineTo(size * 0.13, size * 0.03)
            ctx.arc(0, size * 0.03, size * 0.13, 0, Math.PI)
            ctx.closePath()
            ctx.fill()
            ctx.lineWidth = Math.max(1.4, size * 0.075)
            ctx.beginPath()
            ctx.arc(0, -size * 0.08, size * 0.27, 0, Math.PI)
            ctx.stroke()
            ctx.beginPath()
            ctx.moveTo(0, size * 0.19)
            ctx.lineTo(0, size * 0.37)
            ctx.moveTo(-size * 0.15, size * 0.37)
            ctx.lineTo(size * 0.15, size * 0.37)
            ctx.stroke()
        } else if (kind === "ring") {
            ctx.lineWidth = Math.max(1.6, size * 0.10)
            ctx.beginPath()
            ctx.arc(0, 0, size * 0.28, 0, Math.PI * 2)
            ctx.stroke()
        } else if (kind === "home") {
            ctx.beginPath()
            ctx.moveTo(-size * 0.36, -size * 0.02)
            ctx.lineTo(0, -size * 0.35)
            ctx.lineTo(size * 0.36, -size * 0.02)
            ctx.moveTo(-size * 0.27, -size * 0.08)
            ctx.lineTo(-size * 0.27, size * 0.31)
            ctx.lineTo(size * 0.27, size * 0.31)
            ctx.lineTo(size * 0.27, -size * 0.08)
            ctx.stroke()
        }
        ctx.restore()
    }
}
