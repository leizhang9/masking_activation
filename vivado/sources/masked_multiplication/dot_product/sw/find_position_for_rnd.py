import math

def add_tree(input_vector, level = 0, came_from = ["outside"]):
	global deepest_level, a_index, b_index, a, b, adders_total
	if len(input_vector) == 1:
		print("level: " + str(level) + ", stop_element: " + str(input_vector) + ", came from: " + str(came_from))
	elif len(input_vector) == 2:
		print("level: " + str(level) + ", will_be_added: " + str(input_vector) + ", came from: " + str(came_from))
		adders_total = adders_total + 1
		if level > deepest_level:
			a_index = v_in.index(input_vector[0])
			b_index = v_in.index(input_vector[1])
			deepest_level = level
			a = input_vector[0]
			b = input_vector[1]
	else:
		input_array = list(reversed(input_vector))

		left_tree_input = list(reversed(input_array[math.floor(len(input_array)/2):]))
		right_tree_input = list(reversed(input_array[:math.floor(len(input_array)/2)]))

		print("level: " + str(level) + ", left: " + str(left_tree_input) + ", right: " + str(right_tree_input) + ", came from: " + str(came_from))

		level = level + 1
		adders_total = adders_total + 1

		add_tree(left_tree_input, level, came_from + ["left"])
		add_tree(right_tree_input, level, came_from + ["right"])

for i in range(2,1000):
	deepest_level = -1
	a_index = 0
	b_index = 0
	adders_total = 0
	a = None
	b = None
	v_in = list(reversed(list(range(0, i))))
	print(v_in)
	add_tree(v_in)
	print("--> deepest level: " + str(deepest_level) + ", adders total: " + str(adders_total) + ", a index: " + str(a_index) + ", b index: " + str(b_index) + ", a: " + str(a) + ", b: " + str(b))
