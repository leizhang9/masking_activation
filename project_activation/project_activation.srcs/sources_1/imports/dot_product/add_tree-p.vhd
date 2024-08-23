library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mod_adder_pkg.all;

package add_tree_pkg is

	component add_tree is
		generic (
			num_inputs_g   : positive;
			data_width_g   : positive;
			pipelined_g    : boolean := false
		);
		port (
			clk_i    : in  std_ulogic;
			rst_i    : in  std_ulogic;
			en_i     : in  std_ulogic;
			input_i  : in  std_ulogic_vector(num_inputs_g*data_width_g-1 downto 0);
			output_o : out std_ulogic_vector(data_width_g-1 downto 0)
		);
	end component;

	component mod_adder is
		generic (
			L_g : positive
		);
		port (
			a_i : in  std_ulogic_vector (L_g - 1 downto 0);
			b_i : in  std_ulogic_vector (L_g - 1 downto 0);
			s_o : out std_ulogic_vector (L_g - 1 downto 0)
		);
	end component;


end package add_tree_pkg;

package body add_tree_pkg is

end package body;