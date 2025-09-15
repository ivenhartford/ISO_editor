#include <QApplication>
#include <QFile>
#include "iso_editor.h"
#include "logging_utils.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    setupLogging();

    QFile styleSheetFile(":/stylesheet.qss");
    if (styleSheetFile.open(QFile::ReadOnly)) {
        QString styleSheet = QLatin1String(styleSheetFile.readAll());
        app.setStyleSheet(styleSheet);
    } else {
        qWarning() << "Could not load stylesheet.";
    }

    ISOEditor window;
    window.show();

    return app.exec();
}
