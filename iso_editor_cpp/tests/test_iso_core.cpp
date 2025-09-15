#include "gtest/gtest.h"
#include "iso_core.h"
#include <QTemporaryFile>
#include <QTemporaryDir>
#include <QTextStream>
#include <QFileInfo>

// Test fixture for ISOCore tests
class ISOCoreTest : public ::testing::Test {
protected:
    void SetUp() override {}
    void TearDown() override {}
    ISOCore core;
};

TEST_F(ISOCoreTest, InitialState) {
    ASSERT_NE(core.getDirectoryTree(), nullptr);
    EXPECT_EQ(core.getDirectoryTree()->name, "/");
    EXPECT_EQ(core.isModified(), false);
    EXPECT_EQ(core.getVolumeDescriptor().volumeId, "NEW_ISO");
    EXPECT_EQ(core.getDirectoryTree()->children.size(), 0);
}

TEST_F(ISOCoreTest, AddFolder) {
    IsoNode* root = core.getDirectoryTree();
    core.addFolderToDirectory("TEST_DIR", root);
    ASSERT_EQ(root->children.size(), 1);
    const IsoNode* newDir = root->children.first();
    EXPECT_EQ(newDir->name, "TEST_DIR");
    EXPECT_TRUE(newDir->isDirectory);
    EXPECT_EQ(newDir->parent, root);
    EXPECT_TRUE(core.isModified());
}

TEST_F(ISOCoreTest, AddFile) {
    QTemporaryFile tempFile;
    ASSERT_TRUE(tempFile.open());
    tempFile.write("hello world");
    tempFile.close();
    IsoNode* root = core.getDirectoryTree();
    core.addFileToDirectory(tempFile.fileName(), root);
    ASSERT_EQ(root->children.size(), 1);
    const IsoNode* newFile = root->children.first();
    EXPECT_EQ(newFile->name, QFileInfo(tempFile.fileName()).fileName());
    EXPECT_FALSE(newFile->isDirectory);
    EXPECT_EQ(newFile->size, 11);
    EXPECT_EQ(newFile->parent, root);
    EXPECT_TRUE(core.isModified());
}

TEST_F(ISOCoreTest, RemoveNode) {
    IsoNode* root = core.getDirectoryTree();
    core.addFolderToDirectory("EMPTY_DIR", root);
    core.addFolderToDirectory("DIR_TO_DELETE", root);
    ASSERT_EQ(root->children.size(), 2);
    IsoNode* nodeToDelete = nullptr;
    for (auto* child : root->children) {
        if (child->name == "DIR_TO_DELETE") {
            nodeToDelete = child;
            break;
        }
    }
    ASSERT_NE(nodeToDelete, nullptr);
    core.removeNode(nodeToDelete);
    ASSERT_EQ(root->children.size(), 1);
    const IsoNode* remainingNode = root->children.first();
    EXPECT_EQ(remainingNode->name, "EMPTY_DIR");
    EXPECT_TRUE(core.isModified());
}

TEST_F(ISOCoreTest, AddDuplicateFolder) {
    IsoNode* root = core.getDirectoryTree();
    core.addFolderToDirectory("TEST_DIR", root);
    ASSERT_EQ(root->children.size(), 1);
    core.addFolderToDirectory("TEST_DIR", root);
    EXPECT_EQ(root->children.size(), 1) << "Should not add a folder with a duplicate name";
}

TEST_F(ISOCoreTest, OverwriteFile) {
    QTemporaryDir tempDir;
    ASSERT_TRUE(tempDir.isValid());
    QString filePath = tempDir.filePath("testfile.txt");

    // Create and add the first file
    QFile file1(filePath);
    ASSERT_TRUE(file1.open(QIODevice::WriteOnly));
    file1.write("first version");
    file1.close();
    core.addFileToDirectory(filePath, core.getDirectoryTree());

    ASSERT_EQ(core.getDirectoryTree()->children.size(), 1);
    EXPECT_EQ(core.getDirectoryTree()->children.first()->size, 13);

    // Create and add a second file with the same name
    QFile file2(filePath);
    ASSERT_TRUE(file2.open(QIODevice::WriteOnly));
    file2.write("second, longer version");
    file2.close();
    core.addFileToDirectory(filePath, core.getDirectoryTree());

    ASSERT_EQ(core.getDirectoryTree()->children.size(), 1) << "Overwriting should not increase child count";
    EXPECT_EQ(core.getDirectoryTree()->children.first()->size, 22) << "File size should be updated after overwrite";
}

TEST_F(ISOCoreTest, ImportDirectory) {
    QTemporaryDir tempDir;
    ASSERT_TRUE(tempDir.isValid());

    // Create a nested structure
    QDir(tempDir.path()).mkdir("SUBDIR");
    QFile file1(tempDir.filePath("file1.txt"));
    ASSERT_TRUE(file1.open(QIODevice::WriteOnly));
    file1.write("file1");
    file1.close();
    QFile file2(tempDir.filePath("SUBDIR/file2.txt"));
    ASSERT_TRUE(file2.open(QIODevice::WriteOnly));
    file2.write("file2");
    file2.close();

    // Import the directory
    core.importDirectory(tempDir.path(), core.getDirectoryTree());

    // Assert the structure
    ASSERT_EQ(core.getDirectoryTree()->children.size(), 1);
    const IsoNode* importedDir = core.getDirectoryTree()->children.first();
    EXPECT_EQ(importedDir->name, QFileInfo(tempDir.path()).fileName());
    ASSERT_EQ(importedDir->children.size(), 2);

    const IsoNode* importedFile1 = nullptr;
    const IsoNode* importedSubDir = nullptr;
    for (const auto* child : importedDir->children) {
        if (child->name == "file1.txt") importedFile1 = child;
        if (child->name == "SUBDIR") importedSubDir = child;
    }

    ASSERT_NE(importedFile1, nullptr);
    ASSERT_NE(importedSubDir, nullptr);

    EXPECT_FALSE(importedFile1->isDirectory);
    EXPECT_TRUE(importedSubDir->isDirectory);

    ASSERT_EQ(importedSubDir->children.size(), 1);
    const IsoNode* importedFile2 = importedSubDir->children.first();
    ASSERT_NE(importedFile2, nullptr);
    EXPECT_EQ(importedFile2->name, "file2.txt");
}
