import os
import pkg_resources

                                           
class GPTinstructions:
    def __init__(self, instructions_dir=None):
        if instructions_dir is None:
            # /Users/phil/Dropbox/GITHUB/scrapifurs/scrapifurs/data/instructions/linkedinSearchExtractNamesDF.txt
   
            instructions_dir = pkg_resources.resource_filename('scrapifurs', '/data/instructions/')
        self.instructions_dir = instructions_dir
        self.instructions_dict = {}
        self._load_file_names()

    def _load_file_names(self):
        for file in os.listdir(self.instructions_dir):
            if file.endswith(".txt"):
                key = file[:-4]  # remove the '.txt' extension
                self.instructions_dict[key] = None

    def print_instructions(self):
        for key in self.instructions_dict.keys():
            print(key)

    def get_instruction(self, key):
        if key in self.instructions_dict:
            if self.instructions_dict[key] is None:  # if the data has not been loaded yet
                with open(os.path.join(self.instructions_dir, key + ".txt"), 'r') as file:
                    data = file.read()
                self.instructions_dict[key] = data
            return self.instructions_dict[key]
        else:
            print("No instruction with the given key found.")





# import pkg_resources

# def read_text_file():
#     # Get the path to the text file. This will work no matter where
#     # your package is installed.
#     filepath = pkg_resources.resource_filename('scrapifurs', '../data/your_text_file.txt')

#     # Open the file and read its contents.
#     with open(filepath, 'r') as file:
#         data = file.read()

#     # Return the file's contents.
#     return data
