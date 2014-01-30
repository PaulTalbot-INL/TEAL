'''
Created on Jan 28, 2014
TreeStructure. 2 classes Node, NodeTree
@author: alfoa
'''

#for future compatibility with Python 3--------------------------------------------------------------
from __future__ import division, print_function, unicode_literals, absolute_import
import warnings
warnings.simplefilter('default',DeprecationWarning)
#End compatibility block for Python 3----------------------------------------------------------------

class Node(object):
  def __init__(self, name, valuesin={}):
    '''
      Initialize Tree, 
      @ In, name, String, is the node name
      @ In, valuesin, is a dictionary of values 
    '''
    values         = valuesin.copy()
    self.name      = name
    self.values    = values
    self._branches = []

  def __repr__(self):
    '''
      Overload the representation of this object... We want to show the name and the number of branches!!!!
    '''
    return "<TreeNode %s at 0x%x containing %s branches>" % (repr(self.name), id(self), repr(str(len(self._branches))))

  def copyNode(self):
    '''
      Method to copy this node and return it
      @ In, None
      @ Out, a new istance of this node
    '''
    node = self.__class__(self.name, self.values)
    node[:] = self
    return node

  def numberBranches(self):
    '''
      Method to get the number of branches
      @ In, None
      @ Out, int, number of branches
    '''
    return len(self._branches)

  def appendBranch(self, node):
    '''
      Method used to append a new branch to this node
      @ In, NodeTree, the newer node
    '''
    self._branches.append(node)

  def extendBranch(self, nodes):
    '''
      Method used to append subnodes from a sequence of them
      @ In, list of NodeTree, nodes
    '''
    self._branches.extend(nodes)

  def insertBranch(self, pos, node):
    '''
      Method used to insert a new branch in a given position
      @ In, node, NodeTree, the newer node
      @ In, pos, integer, the position  
    '''
    self._branches.insert(pos, node)

  def removeBranch(self, node):
    '''
      Method used to remove a subnode
      @ In, the node to remove
    '''
    self._branches.remove(node)

  def findBranch(self, path):
    '''
      Method used to find the first matching branch (subnode)
      @ In, path, string, is the name of the branch or the path 
      @ Out, the matching subnode
    '''
    return NodePath.find(self, path)

  def findallBranch(self, path):
    '''
      Method used to find all the matching branches (subnodes)
      @ In, path, string, is the name of the branch or the path 
      @ Out, all the matching subnodes
    '''
    return NodePath.findall(self, path)

  def iterfind(self, path):
    '''
      Method used to find all the matching branches (subnodes)
      @ In, path, string, is the name of the branch or the path 
      @ Out, iterator containing all matching nodes
    '''
    return NodePath.iterfind(self, path)

  def clearBranch(self):
    '''
      Method used clear this node
      @ In, None 
      @ Out, None
    '''
    self.values.clear()
    self._branches = []

  def get(self, key, default=None):
    '''
      Method to get a value from this element tree
      If the key is not present, None is returned
      @ In, key, string, id name of this value
      @ In, default, an optional default value returned if not found
      @ Out, the coresponding value or default
    '''
    return self.values.get(key, default)

  def add(self, key, value):
    '''
      Method to add a new value into this node
      If the key is already present, the corresponding value gets updated 
      @ In, key, string, id name of this value
      @ In, value, whatever type, the newer value
    '''
    self.values[key] = value

  def keys(self):
    '''
      Method to return the keys of the values dictionary
      @ Out, the values keys
    '''
    return self.values.keys()

  def getValues(self):
    '''
      Method to return values dictionary
      @ Out, dict, the values
    '''
    return self.values

  def iter(self, name=None):
    '''
       Creates a tree iterator.  The iterator loops over this node
       and all subnodes and returns all nodes with a matching name.
       @ In, string, name of the branch wanted        
    '''
    if name == "*":
      name = None
    if name is None or self.name == name:
      yield self
    for e in self._branches:
      for e in e.iter(name):
        yield e

#################
#   NODE TREE   #
#################
class NodeTree(object):
  def __init__(self, node=None):
      self._rootnode = node
  
  def getrootnode(self):
      return self._rootnode

  def _setrootnode(self, node):
    '''
      Method used to replace the rootnode with this node
      @ In, the newer node
    '''
    self._rootnode = node

  def iter(self, name=None):
    '''
      Method for creating a tree iterator for the root node
      @ In, name, string, the path or the node name
      @ Out, the iterator
    '''
    return self._rootnode.iter(name)

  def find(self, path):
    '''
      Method to find the first toplevel node with a given name
      @ In, path, string, the path or name
      @ Out, first matching node or None if no node was found
    '''
    if path[:1] == "/":
      path = "." + path
    return self._rootnode.find(path)

  def findall(self, path):
    '''
      Method to find the all toplevel nodes with a given name
      @ In, path, string, the path or name
      @ Out, A list or iterator containing all matching nodes
    '''
    if path[:1] == "/":
      path = "." + path
    return self._rootnode.findall(path)

  def iterfind(self, path):
    '''
      Method to find the all matching subnodes with a given name
      @ In, path, string, the path or name
      @ Out, a sequence of node instances
    '''
    if path[:1] == "/":
      path = "." + path
    return self._rootnode.iterfind(path, namespaces)

####################
#  NodePath Class  #
#  used to iterate #
####################
class NodePath(object):
  def find(self, node, name):
    for nod in node:
      if nod.name == name:
        return nod
    return None
  def iterfind(self, node, name):
    if name[:3] == ".//":
      for nod in node.iter(name[3:]):
        yield nod
      for nod in node:
        if nod.name == name:
          yield nod
  def findall(self, node, name):
    return list(self.iterfind(node, name))

def isnode(node):
  return isinstance(node, TreeNode) or hasattr(node, "name")
