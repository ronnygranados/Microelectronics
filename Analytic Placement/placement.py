import csv
import numpy as np
import matplotlib.pyplot as plt


class AnaliticPlacement:
    def __init__(self, netlist, sitemap):
        self.netlist = netlist
        self.sitemap = sitemap

    # Opens a .csv file containing the respective netlist and
    # converts every value from a string to an integer. Also
    # returns the respective number of cells and ports of the design.
    def open_netlist(self):
        with open(self.netlist) as archive:
            netlist = csv.reader(archive)
            data = list(netlist)

            data = [[int(element) for element in row] for row in data]

            cells, ports = data[0][0], data[0][1]

            return data, cells, ports

    # Based on the connections obtained with the open_netlist function
    # and the number or ports and cells the c_matrix function returns
    # the respective C matrix required for the placement algorithm.
    # This matrix has a size of cellsXcells.
    def c_matrix(self):
        data, cells, ports = self.open_netlist()

        # For the C matrix, not all connections are valid, some of them are
        # cells connected to ports. An array called valid_nets is created to
        # store valid connections between cells only.
        valid_nets = []

        for i in range(1, len(data)):
            # If the first element of one of the lines is greater than 1000
            # that means it is a port so we skip those lines; and if we find
            # a cell but its connected to a port then its not valid either to
            # build the C matrix
            if data[i][0] < 1000 and data[i][1] < 1000:
                valid_nets.append(data[i])

        C_matrix = np.zeros(shape=(cells, cells), dtype=int)

        for row, column in valid_nets:
            C_matrix[row-1][column-1] = 1
            C_matrix[column-1][row-1] = 1

        return C_matrix

    def a_matrix(self):
        # To build the A matrix we need to access to the C matrix and also
        # the cells connected to ports, inlcuded in the 'data' list.
        data, cells, ports = self.open_netlist()
        cell_port_list = []

        for i in range(1, len(data)):
            if data[i][0] >= 1000 or data[i][1] >= 1000:
                cell_port_list.append(data[i])

        c = self.c_matrix()
        a = -self.c_matrix()

        for j in range(len(c)):
            for row in c:
                a[j][j] = sum(row)

        for k in range(len(cell_port_list)):
            if cell_port_list[k][0] < 1000:
                val1 = cell_port_list[k][0]
                a[val1-1][val1-1] += 1
            elif cell_port_list[k][1] < 1000:
                val2 = cell_port_list[k][1]
                a[val2-1][val2-1] += 1

        return a

    def open_sitemap(self):
        with open(self.sitemap) as archive:
            sitemap = csv.reader(archive)
            data = list(sitemap)

            data = [[float(element) for element in row] for row in data]

            return data

    def by_matrix(self):
        netlist, cells, ports = self.open_netlist()
        sitemap = self.open_sitemap()

        # This part of the code creates a cellX1 zeros matrix that
        # will store the Y coordinates of the ports exclusively
        y_coord = np.zeros(shape=(cells, 1), dtype=float)

        for row in range(len(sitemap)):  # 3
            for net in range(1, len(netlist)):  # 8
                if sitemap[row][0] == netlist[net][0]:
                    cell = netlist[net][1]
                    y_coord[cell-1][0] += sitemap[row][2]
                elif sitemap[row][0] == netlist[net][1]:
                    cell = netlist[net][0]
                    y_coord[cell-1][0] += sitemap[row][2]

        return y_coord

    def bx_matrix(self):
        netlist, cells, ports = self.open_netlist()
        sitemap = self.open_sitemap()

        # This part of the code creates a cellX1 zeros matrix that
        # will store the Y coordinates of the ports exclusively
        x_coord = np.zeros(shape=(cells, 1), dtype=float)

        for row in range(len(sitemap)):  # 3
            for net in range(1, len(netlist)):  # 8
                if sitemap[row][0] == netlist[net][0]:
                    cell = netlist[net][1]
                    x_coord[cell-1][0] += sitemap[row][1]
                elif sitemap[row][0] == netlist[net][1]:
                    cell = netlist[net][0]
                    x_coord[cell-1][0] += sitemap[row][1]

        return x_coord

    def calc_positions(self):
        a = self.a_matrix()
        bx = self.bx_matrix()
        by = self.by_matrix()

        x_pos = np.linalg.solve(a, bx)

        y_pos = np.linalg.solve(a, by)

        return x_pos, y_pos

    def coord(self):
        x, y = self.calc_positions()

        points = np.zeros(shape=(len(x), 2), dtype=float)

        for i in range(len(x)):
            points[i][0] = round(x[i][0], 5)
            points[i][1] = round(y[i][0], 5)

        print("Las coordenadas de las celdas optimzadas son:")

        for i in range(len(points)):
            print(f"x{i+1}: {round(points[i][0], 5)} \t\t"
                  f"y{i+1}: {round(points[i][1], 5)}")

        return points

    def plot_points(self):
        x, y = self.calc_positions()
        ports_data = self.open_sitemap()
        netlist, cells, ports = self.open_netlist()

        for i in range(len(x)):
            plt.scatter(x[i], y[i], s=200, edgecolors='black')
            plt.text(x[i], y[i], i+1, ha='center', va='center')

        for i in range(len(x)):
            for j in range(i+1, len(x)):
                plt.plot([x[i], x[j]], [y[i], y[j]], 'b-')

        for i in range(len(ports_data)):
            plt.scatter(ports_data[i][1], ports_data[i][2],
                        s=200, edgecolors='black', marker='s')
            plt.text(ports_data[i][1], ports_data[i][2], ports_data[i][0],
                     ha='right', va='top')

        cell_port = []

        for net in range(len(netlist)):
            if netlist[net][0] >= 1000:
                x_pos = netlist[net][0]
                y_pos = netlist[net][1]
                cell_port.append((x_pos, y_pos))
            elif netlist[net][1] >= 1000:
                x_pos = netlist[net][1]
                y_pos = netlist[net][0]
                cell_port.append((x_pos, y_pos))

        for i in range(len(cell_port)):
            port_info = cell_port[i][0]-1000
            cell_info = cell_port[i][1]-1

            plt.plot([ports_data[port_info][1], x[cell_info][0]],
                     [ports_data[port_info][2], y[cell_info][0]], 'b-')

        plt.xlim(-0.001, 1.001)
        plt.ylim(0, 1)
        plt.show()


if __name__ == "__main__":
    placement = AnaliticPlacement("netlist.csv", "sitemap.csv")
    placement.coord()
    placement.plot_points()
