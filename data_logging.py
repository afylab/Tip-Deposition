'''
Moduels to log and retreive recipe information (parameters, etc) and data
'''
from os import makedirs
from os.path import join, exists

from datetime import datetime

from exceptions import LogFileFormatError

class recipe_logger():
    '''
    Record information on steps to a readable format to a readable format. Each deposition creates
    a row in a .csv file with the parameters entered on the interface. Can also load from these rows.

    Args:
        recipe : The Recipe object to load, the Recipe name and version will determine the file.
        savedir (Path-like) : The directory to save the log to, the name of the log file is determined
            by the Recipe object name and version number. By default uses local 'logs' folder
    '''
    def __init__(self, recipe, savedir=None):
        if savedir is None:
            savedir = 'logs'
            if not exists(savedir):
                makedirs(savedir)
        #
        filename = type(recipe).__name__ + '_v' + recipe.version.replace('.','-')+'_params'+'.csv'
        self.flpath = join(savedir, filename)
        self.col = 0 # The column index

        if exists(self.flpath):
            self.filemode = 'a' # append if already exists, it is assumed to have the correct first line
        else:
            self.filemode = 'w' # create a new file if not, fill buffer and create the first line at the end
    #

    def startlog(self, startupstep):
        '''
        Begin writing to the file, creating if it does not exist and ensuring the proper format. This
        needs to be called before any other call to recipe_logger.log, which will throw an exception otherwise.

        Args:
            startupstep : The initial Step in the Recipe, which is handeled differently by the sequencer.
        '''
        self.writer = open(self.flpath, self.filemode)

        # Grab the first row if it exists
        if self.filemode == 'a':
            with open(self.flpath, 'r') as reader:
                self.firstline = reader.readline().split(',')
                self.firstline[len(self.firstline)-1] = self.firstline[len(self.firstline)-1].rstrip() # Remove trailing \n character
        else:
            self.firstline = []

        # Always make the date the first entry
        s = datetime.now().strftime('%Y/%m/%d')
        if self.filemode == 'w': # If a new file, write the parameter name and buffer the values
            self.firstline.append('Date')
            self.writer.write(self.firstline[self.col])
            self.buffer = s
        else:
            print(self.firstline)
            if self.firstline[self.col] != 'Date':
                raise LogFileFormatError("First column of log file must be Date")
            self.writer.write('\n'+s)
        self.col += 1
        self.log(startupstep)
    #

    def log(self, step):
        '''
        Logs parameters into the log file. Requires that startlog was called previously to initilize
        the file writer or it will throw an exception.

        Args:
            step : The Step object to read from. Will raise an error if the Step has not been processed.
        '''

        # If the top row exists, check that the parameters
        params = step.get_all_params()
        if params is None:
            return
        #

        for name in params.keys():
            s = str(str(params[name])).replace(',','_')
            if self.filemode == 'w': # If a new file, write the parameter name and buffer the values
                self.firstline.append(str(name))
                self.writer.write(',' + self.firstline[self.col])
                self.buffer += ',' + s
            else:
                print(self.col, name, self.firstline[self.col])
                if self.col + 1 > len(self.firstline):
                    errmsg = "Attempting to write parameters past the last column of the log file."
                    errmsg = errmsg + " Usually this means the Recipe was changed without incrementing the version number."
                    raise LogFileFormatError(errmsg)
                elif self.firstline[self.col] != name:
                    errmsg = "Parameter " + name + "does not belong in column " + str(self.col+1) + '.'
                    errmsg = errmsg + " Usually this means the Recipe was changed without incrementing the version number."
                    raise LogFileFormatError(errmsg)
                self.writer.write(',' + s)
            self.col += 1
        self.writer.flush()
    #

    def load(self, squidname=None):
        '''
        Load parameters of a previous run from the log.

        Args:
            squidname (str) : If not None, will load parameters from the row containing the first
                instance of this Squid Name parameter which is assumed to be the second column. If
                None or if squidname cannot be found, will load parameters from the last row.

        Returns:
            Returns a dictionary of strings 'name':'value' where 'name' is the name from the first row
            and 'value' is a string read from the row. If it is a new log returns None.

        Raises:
            LogFileFormatError is the log file is incorrectly formatted.
        '''
        if self.filemode == 'w':
            return None
        else:
            with open(self.flpath, 'r') as reader:
                lines = reader.readlines()
            #
            if len(lines) < 2:
                raise LogFileFormatError("Improperly Formatted Log File")

            firstline = lines[0].split(',')
            firstline[len(firstline)-1] = firstline[len(firstline)-1].rstrip()

            if squidname is None:
                ix = len(lines) - 1
            else:
                ix = -1
                for i in range(1,len(lines)):
                    ln = lines[i].split(',')
                    if ln[1] == squidname:
                        ix = i
                        break
                if ix == -1: # Default to last line if the
                    ix = len(lines) - 1
                    print("SQUID name " + squidname + "not found, loading paramters from last deposition.")

            params = lines[ix].split(',')
            if len(params) != len(firstline) or len(params) < 1:
                raise LogFileFormatError("Improperly Formatted Log File")
            ret = dict()
            for i in range(1, len(params)): # Does not include first entry, which is the date
                ret[firstline[i]] = params[i].rstrip()
            return ret
    #

    def __del__(self):
        '''
        Destructor, to make sure the file object is closed properly. I.e. by filling unused fields with
        empty spaces, adding the top row if it doesn't exist.
        '''
        try: # If the object is closed before startlog is called this will cause exceptions
            if self.filemode == 'w': # If it was a new file, write the buffered paramters
                self.writer.write('\n')
                self.writer.write(self.buffer)
            else: # If you are editing an existing file, and the number of columns doesn't match, fill remaining space with blanks
                while self.col < len(self.firstline):
                    print(self.col, len(self.firstline))
                    self.writer.write(',')
                    self.col += 1
                #
            self.writer.flush()
            self.writer.close()
        except:
            pass
    #
#

class data_logger():
    '''
    Wrapper for data vault to record any status data if needed.
    '''
    def __init__(self, servers):
        pass
    #
#
