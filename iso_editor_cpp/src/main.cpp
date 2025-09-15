#include <QApplication>
#include "iso_editor.h"
#include "logging_utils.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    setupLogging();

    ISOEditor window;
    window.show();

    return app.exec();
}
