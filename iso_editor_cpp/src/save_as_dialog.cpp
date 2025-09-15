#include "save_as_dialog.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFormLayout>
#include <QLineEdit>
#include <QCheckBox>
#include <QPushButton>
#include <QDialogButtonBox>
#include <QFileDialog>

SaveAsDialog::SaveAsDialog(QWidget *parent)
    : QDialog(parent)
{
    setWindowTitle("Save ISO As");
    auto *mainLayout = new QVBoxLayout(this);

    auto *formLayout = new QFormLayout();
    filePathEdit = new QLineEdit(this);
    auto *browseButton = new QPushButton("Browse...", this);
    connect(browseButton, &QPushButton::clicked, this, &SaveAsDialog::browse);

    auto *pathLayout = new QHBoxLayout();
    pathLayout->addWidget(filePathEdit);
    pathLayout->addWidget(browseButton);

    formLayout->addRow("Save to:", pathLayout);

    udfCheckbox = new QCheckBox("Enable UDF Support", this);
    udfCheckbox->setChecked(true);
    formLayout->addRow(udfCheckbox);

    hybridCheckbox = new QCheckBox("Create Hybrid ISO", this);
    hybridCheckbox->setChecked(false);
    formLayout->addRow(hybridCheckbox);

    mainLayout->addLayout(formLayout);

    buttonBox = new QDialogButtonBox(QDialogButtonBox::Save | QDialogButtonBox::Cancel, this);
    connect(buttonBox, &QDialogButtonBox::accepted, this, &QDialog::accept);
    connect(buttonBox, &QDialogButtonBox::rejected, this, &QDialog::reject);
    mainLayout->addWidget(buttonBox);
}

SaveOptions SaveAsDialog::getOptions() const
{
    return {
        filePathEdit->text(),
        udfCheckbox->isChecked(),
        hybridCheckbox->isChecked()
    };
}

void SaveAsDialog::browse()
{
    QString filePath = QFileDialog::getSaveFileName(this, "Save ISO As", "", "ISO Files (*.iso)");
    if (!filePath.isEmpty()) {
        filePathEdit->setText(filePath);
    }
}
