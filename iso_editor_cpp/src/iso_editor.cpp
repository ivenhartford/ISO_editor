#include "iso_editor.h"
#include "iso_core.h"

#include <QApplication>
#include <QMenuBar>
#include <QStatusBar>
#include <QAction>
#include <QFileDialog>
#include <QMessageBox>
#include <QInputDialog>
#include <QSplitter>
#include <QGroupBox>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QTreeWidget>
#include <QTreeWidgetItem>
#include <QHeaderView>


ISOEditor::ISOEditor(QWidget *parent)
    : QMainWindow(parent)
{
    setWindowTitle("ISO Editor");
    setGeometry(100, 100, 800, 600);

    createActions();
    createMenus();
    createMainInterface();
    createStatusBar();

    // Connect actions to slots
    connect(newAction, &QAction::triggered, this, &ISOEditor::newIso);
    connect(openAction, &QAction::triggered, this, &ISOEditor::openIso);
    connect(exitAction, &QAction::triggered, this, &ISOEditor::close);

    refreshView(); // Initial view setup
}

void ISOEditor::createActions()
{
    newAction = new QAction("&New ISO...", this);
    openAction = new QAction("&Open ISO...", this);
    saveAction = new QAction("&Save ISO", this);
    saveAsAction = new QAction("Save ISO &As...", this);
    exitAction = new QAction("E&xit", this);
    addFileAction = new QAction("Add &File...", this);
    addFolderAction = new QAction("Add F&older...", this);
    importDirAction = new QAction("&Import Directory...", this);
    removeAction = new QAction("&Remove Selected", this);
    propertiesAction = new QAction("ISO &Properties...", this);
    refreshAction = new QAction("&Refresh", this);
}

void ISOEditor::createMenus()
{
    fileMenu = menuBar()->addMenu("&File");
    fileMenu->addAction(newAction);
    fileMenu->addAction(openAction);
    fileMenu->addSeparator();
    fileMenu->addAction(saveAction);
    fileMenu->addAction(saveAsAction);
    fileMenu->addSeparator();
    fileMenu->addAction(exitAction);

    editMenu = menuBar()->addMenu("&Edit");
    editMenu->addAction(addFileAction);
    editMenu->addAction(addFolderAction);
    editMenu->addAction(importDirAction);
    editMenu->addSeparator();
    editMenu->addAction(removeAction);
    editMenu->addSeparator();
    editMenu->addAction(propertiesAction);

    viewMenu = menuBar()->addMenu("&View");
    viewMenu->addAction(refreshAction);
}

void ISOEditor::createMainInterface()
{
    auto *centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);
    auto *mainLayout = new QHBoxLayout(centralWidget);

    mainSplitter = new QSplitter(Qt::Horizontal);

    auto *leftPane = new QGroupBox("ISO Properties");
    auto *leftLayout = new QVBoxLayout(leftPane);
    isoInfoLabel = new QLabel();
    isoInfoLabel->setWordWrap(true);
    isoInfoLabel->setAlignment(Qt::AlignTop);
    leftLayout->addWidget(isoInfoLabel);
    volumeNameLabel = new QLabel();
    leftLayout->addWidget(volumeNameLabel);
    leftLayout->addStretch();
    mainSplitter->addWidget(leftPane);

    auto *rightPane = new QGroupBox("ISO Contents");
    auto *rightLayout = new QVBoxLayout(rightPane);
    isoContentsTree = new QTreeWidget();
    isoContentsTree->setHeaderLabels({"Name", "Size", "Date Modified", "Type"});
    isoContentsTree->header()->setSectionResizeMode(0, QHeaderView::Stretch);
    rightLayout->addWidget(isoContentsTree);
    mainSplitter->addWidget(rightPane);

    mainSplitter->setSizes({250, 550});
    mainLayout->addWidget(mainSplitter);
}

void ISOEditor::createStatusBar()
{
    mainStatusBar = statusBar();
}

void ISOEditor::refreshView()
{
    isoContentsTree->clear();

    const IsoNode* rootNode = m_core.getDirectoryTree();
    if (rootNode) {
        auto* rootItem = new QTreeWidgetItem(isoContentsTree, QStringList(rootNode->name));
        populateTreeNode(rootItem, rootNode);
        rootItem->setExpanded(true);
    }

    const VolumeDescriptor& vd = m_core.getVolumeDescriptor();
    volumeNameLabel->setText(QString("Volume Name: %1").arg(vd.volumeId));
    isoInfoLabel->setText(QString("System ID: %1\nVolume Size: %2 blocks\nBlock Size: %3 bytes")
                            .arg(vd.systemId)
                            .arg(vd.volumeSize)
                            .arg(vd.logicalBlockSize));

    mainStatusBar->showMessage(m_core.isModified() ? "Modified" : "Ready");
}

void ISOEditor::populateTreeNode(QTreeWidgetItem *parentItem, const IsoNode *parentNode)
{
    for (const IsoNode* childNode : parentNode->children) {
        QStringList rowData;
        rowData << childNode->name;
        if (childNode->isDirectory) {
            rowData << "" << childNode->date.toString() << "Directory";
        } else {
            rowData << QString::number(childNode->size) << childNode->date.toString() << "File";
        }

        auto* childItem = new QTreeWidgetItem(parentItem, rowData);
        if (!childNode->children.isEmpty()) {
            populateTreeNode(childItem, childNode);
        }
    }
}


void ISOEditor::newIso()
{
    m_core.initNewIso();
    refreshView();
}

void ISOEditor::openIso()
{
    QString filePath = QFileDialog::getOpenFileName(this, "Open Image", "", "Disc Images (*.iso *.cue);;All Files (*)");
    if (filePath.isEmpty()) {
        return;
    }

    if (m_core.loadIso(filePath)) {
        refreshView();
    } else {
        QMessageBox::critical(this, "Error", "Failed to load the selected ISO image.");
    }
}
