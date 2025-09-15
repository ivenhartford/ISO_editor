#ifndef ISOEDITOR_H
#define ISOEDITOR_H

#include <QMainWindow>
#include <QTreeWidget>
#include <QMap>
#include "iso_core.h"
#include "droppable_tree_widget.h"

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
    void newIso();
    void openIso();
    void addFolder();
    void removeSelected();
    void addFile();
    void saveIso();
    void saveIsoAs();
    void showIsoProperties();
    void handleDrop(const QStringList &filePaths);

private:
    void createActions();
    void createMenus();
    void createMainInterface();
    void createStatusBar();
    void refreshView();
    void populateTreeNode(QTreeWidgetItem *parentItem, IsoNode *parentNode);
    IsoNode* getSelectedNode();

    ISOCore m_core;
    bool m_isCueSheetLoaded;
    void updateActions();

    QMap<QTreeWidgetItem*, IsoNode*> m_treeItemMap;

    DroppableTreeWidget *isoContentsTree;
    QLabel *isoInfoLabel;
    QLabel *volumeNameLabel;
    QSplitter *mainSplitter;
    QStatusBar *mainStatusBar;

    QMenu *fileMenu, *editMenu, *viewMenu;
    QAction *newAction, *openAction, *saveAction, *saveAsAction, *exitAction;
    QAction *addFileAction, *addFolderAction, *importDirAction, *removeAction;
    QAction *propertiesAction, *refreshAction;
};

#endif // ISOEDITOR_H
