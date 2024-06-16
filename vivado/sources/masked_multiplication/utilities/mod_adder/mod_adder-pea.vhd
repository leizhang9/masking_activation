library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package mod_adder_pkg is

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

end package mod_adder_pkg;

package body mod_adder_pkg is

end package body;

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library work;

entity mod_adder is
	generic (
		L_g : positive -- number of elements in finite ring
	);
	port (
		a_i : in  std_ulogic_vector (L_g - 1 downto 0);
		b_i : in  std_ulogic_vector (L_g - 1 downto 0);
		s_o : out std_ulogic_vector (L_g - 1 downto 0)
	);
end mod_adder;

architecture rtl of mod_adder is
begin 
	s_o <= std_ulogic_vector(unsigned(a_i) + unsigned(b_i));

end rtl;
