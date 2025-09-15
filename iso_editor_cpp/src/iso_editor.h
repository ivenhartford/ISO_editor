#ifndef ISOEDITOR_H
#define ISOEDITOR_H

#include <QMainWindow>
#include <QMap>
#include "iso_core.h"
#include "droppable_tree_widget.h" // Include the custom widget header

// Forward declarations
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
    // Menu actions
    void newIso();
    void openIso();
    void addFolder();
    void removeSelected();
    void addFile();
    void saveIso();
    void saveIsoAs();
    void showIsoProperties();

    // Other UI slots
    void handleDrop(const QStringList &filePaths);

private:
    // UI setup
    void createActions();
    void createMenus();
    void createMainInterface();
    void createStatusBar();
    void refreshView();
    void populateTreeNode(QTreeWidgetItem *parentItem, IsoNode *parentNode);
    IsoNode* getSelectedNode();

    // Core logic handler
    ISOCore m_core;

    // Map to link UI items to core data nodes
    QMap<QTreeWidgetItem*, IsoNode*> m_treeItemMap;

    // UI Widgets
    DroppableTreeWidget *isoContentsTree;
    QLabel *isoInfoLabel;
    QLabel *volumeNameLabel;
    QSplitter *mainSplitter;
    QStatusBar *mainStatusBar;

    // Menus & Actions
    QMenu *fileMenu;
    QMenu *editMenu;
    QMenu *viewMenu;
    QAction *newAction, *openAction, *saveAction, *saveAsAction, *exitAction;
    QAction *addFileAction, *addFolderAction, *importDirAction, *removeAction;
    QAction *propertiesAction, *refreshAction;
};

#endif // ISOEDITOR_H
