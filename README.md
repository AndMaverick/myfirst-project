# myfirst-project
# Maverick Experiments 🚀

This repository is a sandbox for building and shipping ideas.  
I use it to test concepts, write small utilities, and capture what I’m learning along the way.  

## What You’ll Find Here
- Simple tools and scripts that solve everyday problems ⚡  
- Notes and experiments as I explore new technologies 🔍  
- Foundations for larger projects I’ll grow over time 🌱  

## Current Focus
Building a consistent workflow on GitHub and laying the groundwork for future projects.  

Stay tuned — new drops coming soon.

## 🚀 Scripts

### `word_counter.py`
A simple utility script that counts the number of words in any text file.  

**How it works:**  
- Reads the contents of a text file.  
- Splits the text into words.  
- Outputs the total word count.  

**Quick Example (from the code):**  
```python
def count_words(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
        words = text.split()
        return len(words)



