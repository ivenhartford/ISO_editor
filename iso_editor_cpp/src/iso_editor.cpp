#include "iso_editor.h"
#include "iso_core.h"
#include "save_as_dialog.h"
#include "properties_dialog.h"

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
#include <QFileInfo>


ISOEditor::ISOEditor(QWidget *parent)
    : QMainWindow(parent)
{
    setWindowTitle("ISO Editor");
    setGeometry(100, 100, 800, 600);

    createActions();
    createMenus();
    createMainInterface();
    createStatusBar();

    connect(newAction, &QAction::triggered, this, &ISOEditor::newIso);
    connect(openAction, &QAction::triggered, this, &ISOEditor::openIso);
    connect(addFolderAction, &QAction::triggered, this, &ISOEditor::addFolder);
    connect(removeAction, &QAction::triggered, this, &ISOEditor::removeSelected);
    connect(addFileAction, &QAction::triggered, this, &ISOEditor::addFile);
    connect(saveAction, &QAction::triggered, this, &ISOEditor::saveIso);
    connect(saveAsAction, &QAction::triggered, this, &ISOEditor::saveIsoAs);
    connect(propertiesAction, &QAction::triggered, this, &ISOEditor::showIsoProperties);
    connect(exitAction, &QAction::triggered, this, &ISOEditor::close);
    connect(isoContentsTree, &DroppableTreeWidget::filesDropped, this, &ISOEditor::handleDrop);

    refreshView();
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
    connect(refreshAction, &QAction::triggered, this, &ISOEditor::refreshView);
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
    isoContentsTree = new DroppableTreeWidget();
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
    m_treeItemMap.clear();
    IsoNode* rootNode = m_core.getDirectoryTree();
    if (rootNode) {
        auto* rootItem = new QTreeWidgetItem(isoContentsTree, QStringList(rootNode->name));
        m_treeItemMap[rootItem] = rootNode;
        populateTreeNode(rootItem, rootNode);
        rootItem->setExpanded(true);
    }
    const VolumeDescriptor& vd = m_core.getVolumeDescriptor();
    volumeNameLabel->setText(QString("Volume Name: %1").arg(vd.volumeId));
    isoInfoLabel->setText(QString("System ID: %1").arg(vd.systemId));
    mainStatusBar->showMessage(m_core.isModified() ? "Modified" : "Ready");
}

void ISOEditor::populateTreeNode(QTreeWidgetItem *parentItem, IsoNode *parentNode)
{
    for (IsoNode* childNode : parentNode->children) {
        QStringList rowData;
        rowData << childNode->name;
        if (childNode->isDirectory) {
            rowData << "" << childNode->date.toString() << "Directory";
        } else {
            rowData << QString::number(childNode->size) << childNode->date.toString() << "File";
        }
        auto* childItem = new QTreeWidgetItem(parentItem, rowData);
        m_treeItemMap[childItem] = childNode;
        if (!childNode->children.isEmpty()) {
            populateTreeNode(childItem, childNode);
        }
    }
}

IsoNode* ISOEditor::getSelectedNode()
{
    QList<QTreeWidgetItem*> selectedItems = isoContentsTree->selectedItems();
    if (selectedItems.isEmpty()) return m_core.getDirectoryTree();
    return m_treeItemMap.value(selectedItems.first(), m_core.getDirectoryTree());
}

void ISOEditor::newIso() { m_core.initNewIso(); refreshView(); }

void ISOEditor::openIso()
{
    QString filePath = QFileDialog::getOpenFileName(this, "Open Image", "", "Disc Images (*.iso *.cue);;All Files (*)");
    if (!filePath.isEmpty()) {
        if (m_core.loadIso(filePath)) {
            refreshView();
        } else {
            QMessageBox::critical(this, "Error", "Failed to load the selected ISO image.");
        }
    }
}

void ISOEditor::addFolder()
{
    IsoNode* targetNode = getSelectedNode();
    if (!targetNode->isDirectory) targetNode = targetNode->parent;
    bool ok;
    QString folderName = QInputDialog::getText(this, "New Folder", "Enter folder name:", QLineEdit::Normal, "", &ok);
    if (ok && !folderName.isEmpty()) {
        m_core.addFolderToDirectory(folderName, targetNode);
        refreshView();
    }
}

void ISOEditor::addFile()
{
    IsoNode* targetNode = getSelectedNode();
    if (!targetNode->isDirectory) targetNode = targetNode->parent;
    QStringList filePaths = QFileDialog::getOpenFileNames(this, "Add Files");
    if (!filePaths.isEmpty()) {
        for (const QString &filePath : filePaths) {
            m_core.addFileToDirectory(filePath, targetNode);
        }
        refreshView();
    }
}

void ISOEditor::removeSelected()
{
    IsoNode* nodeToRemove = getSelectedNode();
    if (!nodeToRemove || nodeToRemove == m_core.getDirectoryTree()) return;
    QMessageBox::StandardButton reply = QMessageBox::question(this, "Confirm Removal", QString("Are you sure you want to remove '%1'?").arg(nodeToRemove->name), QMessageBox::Yes|QMessageBox::No);
    if (reply == QMessageBox::Yes) {
        m_core.removeNode(nodeToRemove);
        refreshView();
    }
}

void ISOEditor::saveIso()
{
    if (m_core.getCurrentPath().isEmpty()) {
        saveIsoAs();
    } else {
        if (!m_core.saveIso(m_core.getCurrentPath(), true, false)) {
            QMessageBox::critical(this, "Error", "Failed to save the ISO image.");
        } else {
            QMessageBox::information(this, "Success", "ISO saved successfully.");
            refreshView();
        }
    }
}

void ISOEditor::saveIsoAs()
{
    SaveAsDialog dialog(this);
    if (dialog.exec() == QDialog::Accepted) {
        SaveOptions options = dialog.getOptions();
        if (options.filePath.isEmpty()) return;
        if (!m_core.saveIso(options.filePath, options.useUdf, options.makeHybrid)) {
            QMessageBox::critical(this, "Error", "Failed to save the ISO image.");
        } else {
            QMessageBox::information(this, "Success", "ISO saved successfully.");
            refreshView();
        }
    }
}

void ISOEditor::showIsoProperties()
{
    const VolumeDescriptor& vd = m_core.getVolumeDescriptor();
    IsoProperties props = { vd.volumeId, vd.systemId, m_core.getBootImagePath(), m_core.getEfiBootImagePath() };
    PropertiesDialog dialog(props, this);
    if (dialog.exec() == QDialog::Accepted) {
        IsoProperties newProps = dialog.getProperties();
        VolumeDescriptor newVd = { newProps.volumeId, newProps.systemId };
        m_core.setVolumeDescriptor(newVd);
        m_core.setBootImagePath(newProps.bootImagePath);
        m_core.setEfiBootImagePath(newProps.efiBootImagePath);
        refreshView();
    }
}

void ISOEditor::handleDrop(const QStringList &filePaths)
{
    IsoNode* targetNode = getSelectedNode();
    if (!targetNode->isDirectory) targetNode = targetNode->parent;
    for (const QString& path : filePaths) {
        QFileInfo info(path);
        if (info.isDir()) {
            m_core.importDirectory(path, targetNode);
        } else if (info.isFile()) {
            m_core.addFileToDirectory(path, targetNode);
        }
    }
    refreshView();
}
