-- masked product
-- pipeline latency: adds (ceil(ld(2*1)) + 1 + 3) additional clock cycles

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library work;

use work.dot_product_pkg.all;

entity masked_mul is
	generic (
		L_g           : positive := 32; -- fixed point width
		D_g           : positive := 2 -- number of shares
	);
	port (
		rnd_i      : in  std_ulogic_vector(L_g * (D_g - 1) - 1 downto 0);
		clk_i      : in  std_ulogic;
		rst_i      : in  std_ulogic;
		a_i        : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
		b_i        : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
		c_o        : out std_ulogic_vector (L_g * D_g - 1 downto 0)
	);
end masked_mul;


architecture rtl of masked_mul is

	attribute DONT_TOUCH : string;
	attribute keep : string;

begin 

	masked_mul_inst : entity work.dot_product 
	generic map (
		L_g          => L_g,
		D_g          => D_g,
		in_dim_g     => 1,
		pipelined_g  => true
	) port map (
		rnd_i => rnd_i,
		clk_i => clk_i,
		rst_i => rst_i,
		en_i  => '1',
		a_i   => a_i,
		b_i   => b_i,
		c_o   => c_o
	);

end rtl;
