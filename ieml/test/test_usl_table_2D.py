import unittest

from ieml.usl.decoration.path import path
from ieml.usl.table import UslTable2D
from ieml.usl.usl import usl


class TestUslTable2D(unittest.TestCase):

	def test_table2d_lexeme(self):
		u = usl("[! E:A:.  ()(b.-S:.A:.-'S:.-'S:.-', m1(S: B: T:) m2(y. o. e. u. a. i.)) > E:A:. E:A:. (m1(E:U:T:. E:A:T:. E:S:T:. E:B:T:. E:T:T:.))(k.a.-k.a.-')]")

		root_group0 = path(">role>! E:A:.>content")
		# root_group1 = path(">role>! E:A:.>content>group_1 2>")
		actant_group0 = path(">role>E:A:. E:A:.>flexion")

		table = UslTable2D(u, root_group0, actant_group0)

		cells = table.cells
		self.assertTrue(all(len(cells[0]) == len(row) for row in cells))
		dim = (len(cells), len(cells[0]))
		self.assertEqual((root_group0.deference(u).cardinal, actant_group0.deference(u).cardinal), dim)


	def test_table2d_word(self):
		u = usl("[! E:A:.  ()(b.-S:.A:.-'S:.-'S:.-', m1(S: B: T:) m2(y. o. e. u. a. i.)) > E:A:. E:A:. (m1(E:U:T:. E:A:T:. E:S:T:. E:B:T:. E:T:T:.))(k.a.-k.a.-')]")

		root_group0 = path(">role>! E:A:.>content")
		# root_group1 = path(">role>! E:A:.>content>group_1 2>")
		actant_group0 = path(">role>E:A:. E:A:.>flexion")

		table = UslTable2D(u, root_group0, actant_group0)

		cells = table.cells
		self.assertTrue(all(len(cells[0]) == len(row) for row in cells))
		dim = (len(cells), len(cells[0]))
		self.assertEqual((root_group0.deference(u).cardinal, actant_group0.deference(u).cardinal), dim)


if __name__ == '__main__':
	unittest.main()
