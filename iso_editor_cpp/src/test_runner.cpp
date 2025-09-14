#include "iso_core.h"
#include <iostream>

void printTree(const IsoNode* node, int indent = 0) {
    if (!node) return;

    for (int i = 0; i < indent; ++i) {
        std::cout << "  ";
    }
    std::cout << "- " << node->name.toStdString();
    if (node->isDirectory) {
        std::cout << "/";
    }
    std::cout << std::endl;

    for (const IsoNode* child : node->children) {
        printTree(child, indent + 1);
    }
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <path_to_iso>" << std::endl;
        return 1;
    }

    ISOCore core;
    if (!core.loadIso(argv[1])) {
        std::cerr << "Failed to load ISO: " << argv[1] << std::endl;
        return 1;
    }

    std::cout << "Successfully loaded ISO." << std::endl;
    std::cout << "Volume ID: " << core.getVolumeDescriptor().volumeId.toStdString() << std::endl;
    std::cout << "Contents:" << std::endl;

    printTree(core.getDirectoryTree());

    return 0;
}
