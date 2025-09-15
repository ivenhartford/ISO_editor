#ifndef SAVEASDIALOG_H
#define SAVEASDIALOG_H

#include <QDialog>
#include <QString>

// Forward declarations
class QLineEdit;
class QCheckBox;
class QDialogButtonBox;

struct SaveOptions {
    QString filePath;
    bool useUdf;
    bool makeHybrid;
};

class SaveAsDialog : public QDialog
{
    Q_OBJECT

public:
    explicit SaveAsDialog(QWidget *parent = nullptr);

    SaveOptions getOptions() const;

private slots:
    void browse();

private:
    QLineEdit *filePathEdit;
    QCheckBox *udfCheckbox;
    QCheckBox *hybridCheckbox;
    QDialogButtonBox *buttonBox;
};

#endif // SAVEASDIALOG_H
