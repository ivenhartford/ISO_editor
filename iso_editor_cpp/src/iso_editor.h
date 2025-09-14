#ifndef ISOEDITOR_H
#define ISOEDITOR_H

#include <QMainWindow>
#include <QTreeWidget>
#include "iso_core.h" // Include the core logic header

// Forward declarations of Qt classes
class QAction;
class QLabel;
class QMenu;
class QSplitter;
class QStatusBar;

class ISOEditor : public QMainWindow
{
    Q_OBJECT

public:
    explicit ISOEditor(QWidget *parent = nullptr);

private slots:
    // Slots for menu actions
    void newIso();
    void openIso();
    // ... more slots later

private:
    // Private methods to set up the UI
    void createActions();
    void createMenus();
    void createMainInterface();
    void createStatusBar();
    void refreshView(); // Method to update the UI from the core
    void populateTreeNode(QTreeWidgetItem *parentItem, const IsoNode *parentNode);

    // Core logic handler
    ISOCore m_core;

    // UI Widgets
    QTreeWidget *isoContentsTree;
    QLabel *isoInfoLabel;
    QLabel *volumeNameLabel;
    QSplitter *mainSplitter;
    QStatusBar *mainStatusBar;

    // Menus
    QMenu *fileMenu;
    QMenu *editMenu;
    QMenu *viewMenu;

    // Actions
    QAction *newAction;
    QAction *openAction;
    QAction *saveAction;
    QAction *saveAsAction;
    QAction *exitAction;
    QAction *addFileAction;
    QAction *addFolderAction;
    QAction *importDirAction;
    QAction *removeAction;
    QAction *propertiesAction;
    QAction *refreshAction;
};

#endif // ISOEDITOR_H
