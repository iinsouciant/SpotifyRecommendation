from typing import Any

class Node():
    def __init__(self, value=None, next=None):
        self.next: Node|None = None
        self.value: Any = value

    def __repr__(self):
        output = f"{self.value} -> "
        current = self.next
        while current is not None:
            output += f"{current.value} -> "
            current = current.next
        output += "None"
        return output
    
class LinkedList():
    def __init__(self):
        self.head: Node|None = None
        self.__size: int = 0

    def __repr__(self):
        output = ""
        nextNode = self.head
        while nextNode is not None:
            output += f"{nextNode.value} -> "
            nextNode = nextNode.next
        output += "None"
        return output

    def __len__(self) -> int:
        """ Return number of nodes in LinkedList"""
        if self.head and self.__size == 0:
            self.__recount()
        return self.__size
    
    def __getitem__(self, index) -> Any:
        if self.head:
            current = self.head
            i = 0
            while (i < index):
                current = current.next
                i += 1
                if current is None:
                    raise IndexError
            return current.value
        raise IndexError
    
    def __recount(self) -> int:
        self.__size = 0
        current = self.head
        while current is not None:
            self.__size += 1
            current = current.next
        return self.__size

    def prepend(self, val) -> None: 
        aNode = Node()
        aNode.value = val
        aNode.next, self.head = self.head, aNode
        self.__size += 1

    def append(self, val) -> None:
        if (type(val) is list) or (type(val) is tuple):
            i = 0
            if self.head is None:
                self.head = Node(val[i])
                i += 1
            current = self.head
            while current.next is not None:
                current = current.next
            while i < len(val):
                self.__size += 1
                current.next = Node(val[i])
                current = current.next
            return
        else:
            aNode = Node(val)
            if self.head:
                current = self.head
                while current.next is not None:
                    current = current.next
                current.next = aNode
                self.__size += 1
                return
            self.head = aNode
    
    def insertAfter(self, index, val) -> None:
        if self.head is None:
            self.head = Node(val)
            return
        current = self.head
        i = 0
        while (i < index):
            current = current.next
            i += 1
            if current is None:
                raise IndexError
        aNode = Node(val)
        aNode.next = current.next
        current.next = aNode
        self.__size += 1

    def remove(self, index) -> Any:
        current = self.head
        prev = None
        i = 0
        while (i < index) and (current is not None):
            prev = current
            current = current.next
            i += 1
        if current is None:
            raise IndexError
        if prev is None:
            self.head = current.next
        else:
            prev.next = current.next
            self.__size -= 1
        return current.value

    # precondition: give me a target that can be evaluated with == operator against the data
    # postcondition: return the node if one exists, else None
    def search(self, target) -> int:
        i = 0
        if self.head:
            current = self.head
            while current.value != target:
                current = current.next
                i += 1
                if current is None:
                    return -1
            return i 
        return -1 


if __name__ == "__main__":
    a = LinkedList()
    a.prepend(1)
    print(a)
    a.append(-3)
    print(a)
    a.insertAfter(1,3)
    print(a)
    a.append([2,4,6])
    print(a)
    print(a.search(4))
    a.insertAfter(1,7)
    print(a)
    a.remove(3)
    print(a)
    