#include <QApplication>
#include <QMainWindow>
#include <QPushButton>
#include <QVBoxLayout>
#include <QLabel>
#include <QMessageBox>
#include <QDebug>

#include "dialogs/PropertiesDialog.h"
#include "core/ISOCore.h"
#include "Constants.h"

/**
 * @brief Simple test window for PropertiesDialog proof of concept
 *
 * This demonstrates that the Qt/C++ port works correctly.
 * This will be replaced by the full MainWindow implementation.
 */
class TestWindow : public QMainWindow {
    Q_OBJECT

public:
    TestWindow() : core(new ISOCore()) {
        setWindowTitle(QString("%1 - Proof of Concept").arg(Constants::APP_NAME));
        setMinimumSize(400, 300);

        // Create central widget
        auto* centralWidget = new QWidget(this);
        auto* layout = new QVBoxLayout(centralWidget);

        // Info label
        auto* infoLabel = new QLabel(
            "ISO Editor Qt/C++ Proof of Concept\n\n"
            "This demonstrates the PropertiesDialog\n"
            "ported from Python/PySide6 to C++/Qt6.\n\n"
            "Click the button below to test the dialog.",
            this
        );
        infoLabel->setAlignment(Qt::AlignCenter);
        layout->addWidget(infoLabel);

        // Test button
        auto* testButton = new QPushButton("Open Properties Dialog", this);
        testButton->setMinimumHeight(40);
        connect(testButton, &QPushButton::clicked, this, &TestWindow::openPropertiesDialog);
        layout->addWidget(testButton);

        // Status label
        statusLabel = new QLabel("Ready", this);
        statusLabel->setAlignment(Qt::AlignCenter);
        statusLabel->setStyleSheet("QLabel { color: green; font-weight: bold; }");
        layout->addWidget(statusLabel);

        layout->addStretch();

        setCentralWidget(centralWidget);

        // Initialize ISO core
        core->initNewIso();
        updateStatus();
    }

    ~TestWindow() {
        delete core;
    }

private slots:
    void openPropertiesDialog() {
        qDebug() << "Opening PropertiesDialog...";

        PropertiesDialog dialog(core, this);

        if (dialog.exec() == QDialog::Accepted) {
            // User clicked OK - update the ISO core
            core->setVolumeId(dialog.getVolumeId());
            core->setSystemId(dialog.getSystemId());
            core->setBootImagePath(dialog.getBootImagePath());
            core->setEfiBootImagePath(dialog.getEfiBootImagePath());
            core->setBootEmulationType(dialog.getEmulationType());

            updateStatus();

            QMessageBox::information(
                this,
                "Properties Updated",
                QString("Volume ID: %1\n"
                        "System ID: %2\n"
                        "Boot Image: %3\n"
                        "EFI Boot: %4\n"
                        "Emulation: %5")
                    .arg(dialog.getVolumeId())
                    .arg(dialog.getSystemId())
                    .arg(dialog.getBootImagePath().isEmpty() ? "(none)" : dialog.getBootImagePath())
                    .arg(dialog.getEfiBootImagePath().isEmpty() ? "(none)" : dialog.getEfiBootImagePath())
                    .arg(dialog.getEmulationType())
            );

            qDebug() << "Properties updated successfully";
        } else {
            qDebug() << "Dialog cancelled";
        }
    }

    void updateStatus() {
        QString status = QString("Volume: %1 | System: %2 | Modified: %3")
            .arg(core->getVolumeId())
            .arg(core->getSystemId())
            .arg(core->isModified() ? "Yes" : "No");

        statusLabel->setText(status);
    }

private:
    ISOCore* core;
    QLabel* statusLabel;
};

int main(int argc, char* argv[]) {
    QApplication app(argc, argv);

    // Set application metadata
    QApplication::setApplicationName(Constants::APP_NAME);
    QApplication::setApplicationVersion(Constants::VERSION);
    QApplication::setOrganizationName(Constants::APP_AUTHOR);

    qDebug() << "Starting" << Constants::APP_NAME << "version" << Constants::VERSION;
    qDebug() << "Proof of Concept - PropertiesDialog Test";

    TestWindow window;
    window.show();

    return app.exec();
}

#include "main.moc"
