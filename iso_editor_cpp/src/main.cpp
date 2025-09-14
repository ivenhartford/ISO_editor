#include <QApplication>
#include "iso_editor.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);

    ISOEditor window;
    window.show();

    return app.exec();
}
