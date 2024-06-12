#!/usr/bin/python3
import collections


class NodeAlreadyExistsError(Exception):
    def __init__(self, a_node):
        self.message = 'Node already exists: {}'.format(a_node)
        super(NodeAlreadyExistsError, self).__init__(self.message)


class NodeNotExistError(Exception):
    def __init__(self, a_node_name):
        self.message = f'Node(nid={a_node_name}) not exist!'
        super(NodeNotExistError, self).__init__(self.message)


class Tree(object):
    def __init__(self, nid, tag=None, parent=None, data=None):
        self.nid = nid
        self.tag = nid if tag is None else tag
        self.data = data
        self.parent = parent
        self.child = collections.OrderedDict()
        self.level = parent.level + 1 if parent else 1
        self.__print_level = 0

    def __str__(self):
        return f'<Tree object: tag={self.tag} nid={self.nid} data={self.data}>'

    def __repr__(self):
        return f'<Tree object: tag={self.tag} nid={self.nid} data={self.data}>'

    def add_child(self, nid, tag=None, data=None):
        """
        Add a subtree.

        The subtree is ordered. The first to enter is the first.
        :param tag:
        :param nid:
        :param data:
        :return: A subtree node obj.

        """
        tag = nid if tag is None else tag
        if nid not in self.child.keys():
            new_node = Tree(tag=tag, nid=nid, parent=self, data=data)
            self.child[nid] = new_node
            return new_node
        else:
            raise NodeAlreadyExistsError(self.child.get(nid))

    def insert_child(self, nid, p_nid, tag=None, data=None):
        tag = nid if tag is None else tag
        parent = self.get_child(nid=p_nid)
        node = parent.add_child(nid=nid, tag=tag, data=data)
        return node

    @classmethod
    def __get_path(cls, parent_node, path_list: list):
        if parent_node is None:
            return path_list
        else:
            path_list.append(parent_node.tag)
            return cls.__get_path(parent_node=parent_node.parent,
                                  path_list=path_list)

    def path(self):
        """
        Return the path from this node to the root node.

        :return: a path list
        """
        return self.__get_path(parent_node=self.parent, path_list=[self.tag])

    @classmethod
    def __get_child(cls, node, nid, target_node: list):
        for cld in node.child.values():
            if nid == cld.nid:
                target_node.append(cld)
                break
            cls.__get_child(cld, nid, target_node)
            if target_node:
                break

    def get_child(self, nid):
        target = []
        self.__get_child(node=self, nid=nid, target_node=target)
        if not target:
            raise NodeNotExistError(nid)
        return target[0]

    @classmethod
    def __get_nodes_depth(cls, node, node_list: list):
        for cld in node.child.values():
            node_list.append(cld)
            if len(cld.child) == 0:
                continue
            cls.__get_nodes_depth(cld, node_list)

    @classmethod
    def __get_nodes_breadth(cls, node, a_queue: list, node_list: list):
        for cld in node.child.values():
            if len(cld.child) != 0:
                a_queue.append(cld)
            node_list.append(cld)
        if a_queue:
            c_node = a_queue.pop(0)
            cls.__get_nodes_breadth(c_node, a_queue, node_list)

    def nodes(self, depth_first=True):
        node_list = [self]
        if depth_first:
            self.__get_nodes_depth(node=self, node_list=node_list)
        else:
            a_queue = []
            self.__get_nodes_breadth(node=self, a_queue=a_queue,
                                     node_list=node_list)
        return node_list

    def get_parent(self):
        pass

    @classmethod
    def __print_tree(cls, node, indent: list, final_node=True):
        """
        Like:
        .
        └──Tree1
           ├──a
           │  └──a11
           │     ├──a11-1
           │     └──a11-2
           ├──b
           └──c
        :param node:
        :param indent:
        :param final_node:
        :return:
        """
        for i in range(node.__print_level):
            print(indent[i], end='')
        if final_node:
            print('└──', end='')
        else:
            print('├──', end='')
        print(node.tag)
        if len(node.child) == 0:
            return
        else:
            cnt = len(node.child)
            for i, n in enumerate(list(node.child.values())):
                n.__print_level = node.__print_level + 1
                c = '   ' if final_node else '│  '
                indent.append(c)
                last_node = i == cnt - 1
                cls.__print_tree(n, indent, last_node)
                del indent[-1]

    def show(self):
        """
        Print Tree

        :return: None
        """
        self.__print_level = 0
        print('.')
        self.__print_tree(node=self, indent=[], final_node=True)

    @classmethod
    def __get_leaves(cls, node, leaves_list: list):
        if len(node.child) == 0:
            leaves_list.append(node)
        else:
            for cld in node.child.values():
                cls.__get_leaves(cld, leaves_list)

    def leaves(self):
        leaves_list = []
        self.__get_leaves(node=self, leaves_list=leaves_list)
        return leaves_list

    @classmethod
    def __get_depth(cls, node, a_stack: list, max_depth: list):
        if len(node.child) == 0:
            a_stack.append(node)
            max_depth[0] = max(max_depth[0], len(a_stack))
            a_stack.pop()
        else:
            for cld in node.child.values():
                a_stack.append(node)
                cls.__get_depth(cld, a_stack, max_depth)
                a_stack.pop()
    '''
    @classmethod
    def __get_depth(cls, node, q: list, max_depth: list):
        if len(node.child) == 0:
            q.append(node)
            max_depth[0] = max(max_depth[0], len(q))
            q = []
        else:
            for cld in node.child.values():
                q.append(node)
                cls.__get_depth(cld, q, max_depth)
                q = []
    '''

    def depth(self):
        depth_list = [0]
        self.__get_depth(node=self, a_stack=[], max_depth=depth_list)
        return depth_list[0]

    def is_leaves(self):
        return False if self.child else True


def main():
    print('>>> ', "-------- For Example -------")
    print('>>> ', "root = Tree(nid='root', data={})")
    root = Tree(nid='root', data={})

    print('>>> ', "node_A = root.add_child(nid='A')")
    node_A = root.add_child(nid='A')

    print('>>> ', "node_B = root.add_child(nid='B')")
    node_B = root.add_child(nid='B')

    print('>>> ', "node_C = root.add_child(nid='C')")
    node_C = root.add_child(nid='C')

    print('>>> ', "node_A_1 = node_A.add_child(nid='A-1')")
    node_A_1 = node_A.add_child(nid='A-1')

    print('>>> ', "node_A_2 = node_A.add_child(nid='A-2')")
    node_A_2 = node_A.add_child(nid='A-2')

    print('>>> ', "node_C_1 = node_C.add_child(nid='C-1')")
    node_C_1 = node_C.add_child(nid='C-1')

    print('>>> ', "node_A_2_1 = node_A_2.add_child(nid='A-2-1')")
    node_A_2_1 = node_A_2.add_child(nid='A-2-1')

    print('>>> ', "node_A_2_2 = root.insert_child(nid='A-2-2', p_nid='A-2')")
    node_A_2_2 = root.insert_child(nid='A-2-2', p_nid='A-2')

    print('>>> ', "node_A_2_2_1 = node_A_2_2.add_child(nid='A-2-2-1')")
    node_A_2_2_1 = node_A_2_2.add_child(nid='A-2-2-1')

    print('>>> ', "root.show()")
    root.show()

    print('>>> ', "root.depth()")
    print(root.depth())

    print('>>> ', "root.level")
    print(root.level)

    print('>>> ', "root.path()")
    print(root.path())

    print('>>> ', "root.leaves()")
    print(root.leaves(), end='\n\n')

    print('>>> ', "root.nodes(depth_first=False)")
    print(root.nodes(depth_first=False), end='\n\n')

    print('>>> ', "root.nodes(depth_first=True)")
    print(root.nodes(depth_first=True), end='\n\n')

    print('>>> ', "node_A_2 = root.get_child('A-2')")
    node_A_2 = root.get_child('A-2')
    print(node_A_2)

    print('>>> ', "node_A_2.show()")
    node_A_2.show()

    print('>>> ', "node_A_2.depth()")
    print(node_A_2.depth())

    print('>>> ', "node_A_2.level")
    print(node_A_2.level)

    print('>>> ', "node_A_2.path()")
    print(node_A_2.path())

    print('>>> ', "node_A_2.leaves()")
    print(node_A_2.leaves())

    print('>>> ', "node_A_2.nodes()")
    print(node_A_2.nodes())



if __name__ == '__main__':
    main()




