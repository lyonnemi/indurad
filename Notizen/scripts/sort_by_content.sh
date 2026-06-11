#!/bin/bash

# Script: link_by_content.sh
# Usage: ./link_by_content.sh <folder_path> <content_name>
# Description: Searches .md and .txt files for content, creates a directory
#              with the content name inside ../links/, and creates symbolic links

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if correct number of arguments provided
if [ $# -ne 2 ]; then
    echo -e "${RED}Error: Invalid number of arguments${NC}"
    echo "Usage: $0 <folder_path> <content_name>"
    echo "Example: $0 /path/to/notes git"
    echo "Example: $0 ./documents python"
    exit 1
fi

# Assign arguments
FOLDER_PATH="$1"
CONTENT_NAME="$2"

# Remove trailing slash if present
FOLDER_PATH="${FOLDER_PATH%/}"

# Check if folder exists
if [ ! -d "$FOLDER_PATH" ]; then
    echo -e "${RED}Error: Folder '$FOLDER_PATH' does not exist${NC}"
    exit 1
fi

# Create directory structure: ../links/content_name_links/
LINKS_BASE_DIR="../links"
OUTPUT_DIR="${LINKS_BASE_DIR}/${CONTENT_NAME}_links"

# Create the directory (including parent if needed)
mkdir -p "$OUTPUT_DIR"

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Searching for '$CONTENT_NAME' in${NC}"
echo -e "${BLUE}Path: $FOLDER_PATH${NC}"
echo -e "${BLUE}Output directory: $OUTPUT_DIR${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Counter for found files
FOUND_COUNT=0

# Find all .md and .txt files and search for content
while IFS= read -r file; do
    # Search for content name (case insensitive)
    if grep -q -i "$CONTENT_NAME" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓ Found:${NC} $file"
        
        # Get just the filename without path
        filename=$(basename "$file")
        
        # Create unique filename if duplicate exists
        target_link="$OUTPUT_DIR/$filename"
        base_name="${filename%.*}"
        extension="${filename##*.}"
        counter=1
        
        while [ -e "$target_link" ]; do
            target_link="$OUTPUT_DIR/${base_name}_${counter}.${extension}"
            ((counter++))
        done
        
        # Create symbolic link
        # Get absolute path of the original file
        if [[ "$file" = /* ]]; then
            # File already has absolute path
            abs_path="$file"
        else
            # Convert relative path to absolute
            abs_path="$(cd "$(dirname "$file")" && pwd)/$(basename "$file")"
        fi
        
        if ln -s "$abs_path" "$target_link"; then
            echo -e "${YELLOW}  ↳ Linked to:${NC} $target_link"
            ((FOUND_COUNT++))
        else
            echo -e "${RED}  ✗ Failed to create link for: $file${NC}"
        fi
        echo ""
    fi
done < <(find "$FOLDER_PATH" -type f \( -name "*.md" -o -name "*.txt" \) -print0 | xargs -0)

# Print summary
echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}Summary:${NC}"
echo -e "  Content searched: '$CONTENT_NAME'"
echo -e "  Files found: $FOUND_COUNT"
echo -e "  Links created in: $OUTPUT_DIR/"
echo -e "${BLUE}=================================${NC}"

if [ $FOUND_COUNT -eq 0 ]; then
    echo -e "${YELLOW}No matching files found. Removing empty directory...${NC}"
    rmdir "$OUTPUT_DIR" 2>/dev/null
    # Try to remove links directory if empty
    rmdir "$LINKS_BASE_DIR" 2>/dev/null
    exit 0
fi

# Optional: List the created links
echo ""
echo -e "${BLUE}Created links:${NC}"
ls -la "$OUTPUT_DIR/"
