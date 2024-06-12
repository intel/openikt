import xlsxwriter

from lib.narytree import Tree


class NewXlsx(xlsxwriter.Workbook):
    def __init__(self, filename=None, options=None,):
        super(NewXlsx, self).__init__(filename, options)
        self.__cell_style_padding = 4

    def add_worksheet(self, name=None, worksheet_class=None):
        """
        Add a new worksheet to the Excel workbook.

        Args:
            name: The worksheet name. Defaults to 'Sheet1', etc.
            title_tree: A N-Ary tree obj.

        Returns:
            Reference to a worksheet object.

        """
        if worksheet_class is None:
            worksheet_class = self.worksheet_class
        sheet_obj = self._add_sheet(name, worksheet_class=worksheet_class)
        sheet_obj.title_tree = Tree(nid='root', tag=name)
        sheet_obj.row_count = 0
        return sheet_obj

    def write_worksheet(self, sheet_obj):
        """
        Get data from the sheet_obj.title_tree attribute
        and write the data into this sheet table.

        sheet_obj.title_tree is a N-arg tree obj.
        Get from narytree.Tree().
        """
        title_tree = sheet_obj.title_tree
        t_depth = title_tree.depth()
        t_leaves = title_tree.leaves()
        t_first_level = title_tree.child
        column = 0
        # Draw the header rows of the sheet
        for a_item in t_first_level.values():
            # update node.data['width']
            if not a_item.data.get('width'):
                a_item.data['width'] = max(
                    [len(v) for v in str(a_item.tag).split('\n')]
                ) + self.__cell_style_padding
            column_count = len(a_item.leaves())
            column_flag = {}
            all_nodes = a_item.nodes(depth_first=True)
            for node in all_nodes:
                n_tag = node.tag
                n_level = node.level
                row = n_level - a_item.level
                clm = column_flag.get(row, column)
                node_cols = len(node.leaves())
                end_clm = clm + node_cols - 1
                node_data = node.data
                style = node_data.get('style')
                abs_width = node_data.get('abs_width')
                # update node.data['width']
                if not node.data.get('width') and not abs_width:
                    node.data['width'] = max(
                        [len(v) for v in str(n_tag).split('\n')]
                    ) + self.__cell_style_padding
                if node.is_leaves() and n_level < t_depth:
                    sheet_obj.merge_range(
                        row, clm,
                        row + (t_depth - n_level), clm,
                        n_tag,
                        style
                    )
                elif node_cols > 1:

                    sheet_obj.merge_range(
                        row, clm,
                        row, end_clm,
                        n_tag,
                        style
                    )
                else:
                    sheet_obj.write(row, clm, n_tag, style)
                column_flag[row] = end_clm + 1
            column = column + column_count

        for col, node in enumerate(t_leaves):
            node_data = node.data
            abs_width = node_data.get('abs_width')
            start_row = t_depth - 1
            for a_cell in node_data.get('column_cells_list'):
                a_cell_value, a_cell_style, a_cell_rows = a_cell
                if a_cell_rows > 1:
                    sheet_obj.merge_range(
                        start_row, col,
                        start_row+a_cell_rows-1, col,
                        a_cell_value,
                        a_cell_style
                    )
                    start_row += a_cell_rows
                else:
                    sheet_obj.write(
                        start_row, col,
                        a_cell_value,
                        a_cell_style
                    )
                    start_row += 1
                if not abs_width:
                    value_max_length = max(
                        [len(v) for v in str(a_cell_value).split('\n')]
                    )
                    if value_max_length > node_data['width']:
                        node_data['width'] = value_max_length + self.__cell_style_padding
                        node.data = node_data
            node_data['row'] = start_row - 1
            node.data = node_data
            if node_data.get('width'):
                sheet_obj.set_column(col, col, width=node.data.get('width'))


    def get_tree_node_format_data(self, width: int = 0,
                                  row: int = 0,
                                  column_cells_list: list = [],
                                  abs_width: bool = False,
                                  style=None, **kwargs):
        """ Provide a standard data format

        :param width: Cell width.
        :param column_cells_list: A column of cell data. The elements
            in the list come from the  get_tree_node_format_cell() function
        :param row: Record the number of rows in the column where the node
            is located. start from 0
        :param style: Cell Style. get form the add_worksheet() function.
        :param kwargs:
        :return: A formatted dictionary that can be recognized by
            the write_worksheet() function.
        """
        # The list is a variable data type, singleton mode will appear
        # when the default value in the parameter is used
        column_cells_list = column_cells_list if column_cells_list else list()

        return dict(style=style, width=width, row=row,
                    column_cells_list=column_cells_list,
                    abs_width=abs_width, **kwargs)


    def get_tree_node_format_cell(self, value=None, style=None, rows: int = 1):
        """Provide a standard data format

        :param value: The value in the cell.
        :param style: Cell Style.  get form the add_worksheet() function.
        :param rows: Number of rows to be merged.
        :return: A tuple(). (value, style, rows)
        """
        return value, style, rows


def main():
    """For Example

    run: python3 ourxlsx.py
    """

    # Initialize an xlsx file object
    wb = NewXlsx(
        filename='123.xlsx',
        options={
            # global settings
            'string_to_number': True,
            'constant_memory': False,
            'default_format_properties': {
                'font_name': 'Calibri',
                'font_size': 10,
                'align': 'left',
                'valign': 'vcenter',
                'text_wrap': False,
            }
        }
    )

    # Create some styles
    style1 = wb.add_format(
            {'bold': True,
             'font_size': 10,
             'align': 'center',
             'bg_color': 'green',
             'border': 1}
    )
    style2 = wb.add_format(
            {'bold': True,
             'font_size': 10,
             'align': 'center',
             'bg_color': 'red',
             'border': 1}
    )

    # Create a new sheet
    test_sheet = wb.add_worksheet('test_sheet')

    # Make the column titles tree of the sheet
    title_tree = test_sheet.title_tree
    t1 = title_tree.add_child(
        nid='Title0',
        data=wb.get_tree_node_format_data()
    )
    title_tree.add_child(
        nid='Title1: A Sheet Testing',
        data=wb.get_tree_node_format_data(style=style2))
    c1 = title_tree.insert_child(
        nid='Column 1', p_nid='Title1: A Sheet Testing',
        data=wb.get_tree_node_format_data(width=10, style=style1))
    c2 = title_tree.insert_child(
        nid='Column 2', p_nid='Title1: A Sheet Testing',
        data=wb.get_tree_node_format_data(width=10, style=style1))

    # add the data of the sheet to the leaves-nodes of the title tree by column
    test_data = [
        {'c1': 'Test Value1 XXXXXXXXX\nvvvvvv', 'c2': ['1', '2']},
        {'c1': 'Test Value2', 'c2': ['1', '2', '3']}
    ]

    for _data in test_data:
        c1_cell_list = c1.data.get('column_cells_list')
        c1_cell_list.append(
            wb.get_tree_node_format_cell(
                value=_data.get('c1'),
                rows=len(_data.get('c2'))
            )
        )
        # c1.data['column_cells_list'] = c1_cell_list

        c2_cell_list = c2.data.get('column_cells_list')
        for c2_value in _data.get('c2'):
            c2_cell_list.append(wb.get_tree_node_format_cell(value=c2_value))
        # c2.data['column_cells_list'] = c2_cell_list
    t1.data['column_cells_list'].append(
        wb.get_tree_node_format_cell(value='HHHH')
    )
    t1.data['column_cells_list'].append(
        wb.get_tree_node_format_cell(value='HHHH1')
    )
    t1.data['column_cells_list'].append(
        wb.get_tree_node_format_cell(value='HHHH')
    )
    t1.data['column_cells_list'].append(
        wb.get_tree_node_format_cell(value='HHHH1')
    )
    # print the sheet title_tree (debug)
    title_tree.show()

    # write data to sheet in columns
    wb.write_worksheet(test_sheet)
    # save xlsx file
    wb.close()

    print('For Example: save file ./123.xlsx')
    print(c1.data['width'])


if __name__ == "__main__":
    main()
