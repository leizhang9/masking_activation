library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package dot_product_pkg is

	component dot_product is
		generic (
			L_g           : positive; -- fixed point width
			D_g           : positive; -- number of shares
			in_dim_g      : positive;
			pipelined_g   : boolean   := false
		);
		port (
			rnd_i      : in  std_ulogic_vector(L_g * (D_g - 1) - 1 downto 0);
			clk_i      : in  std_ulogic;
			rst_i      : in  std_ulogic;
			en_i       : in  std_ulogic;
			a_i        : in  std_ulogic_vector (L_g * D_g * in_dim_g - 1 downto 0);
			b_i        : in  std_ulogic_vector (L_g * D_g * in_dim_g - 1 downto 0);
			c_o        : out std_ulogic_vector (L_g * D_g - 1 downto 0)
		);
	end component;

end package dot_product_pkg;

package body dot_product_pkg is

end package body;