-- Pipelined modulo multiplier
-- c = a * b mod 32
-- a, b, c are 32 bit
-- latency: 2 clock cycles
-- 3 x 16 bit multiplications in parallel
-- 2 x 16 bit adders in parallel
-- 6 x 32 bit registers

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package mod_multiplier_32_pkg is

	component mod_multiplier_32 is
		port (
			a_i   : in  std_ulogic_vector (31 downto 0);
			b_i   : in  std_ulogic_vector (31 downto 0);
			p_o   : out std_ulogic_vector (31 downto 0);
			clk_i : in  std_ulogic;
			rst_i : in  std_ulogic
		);
	end component;

end package mod_multiplier_32_pkg;

package body mod_multiplier_32_pkg is

end package body;

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library work;

entity mod_multiplier_32 is
	port (
		a_i   : in  std_ulogic_vector (31 downto 0);
		b_i   : in  std_ulogic_vector (31 downto 0);
		p_o   : out std_ulogic_vector (31 downto 0);
		clk_i : in  std_ulogic;
		rst_i : in  std_ulogic
	);
end mod_multiplier_32;

architecture rtl of mod_multiplier_32 is

	signal temp1_s : unsigned (31 downto 0);
	signal temp2_s : unsigned (31 downto 0);
	signal temp3_s : unsigned (31 downto 0);
	signal temp4_s : unsigned (31 downto 0);
	signal temp5_s : unsigned (31 downto 0);

	signal temp1_reg   : unsigned (31 downto 0);
	signal temp2_0_reg : unsigned (31 downto 0);
	signal temp2_1_reg : unsigned (31 downto 0);
	signal temp3_reg   : unsigned (31 downto 0);
	signal temp4_reg   : unsigned (31 downto 0);
	signal temp5_reg   : unsigned (31 downto 0);


begin 
	-- p_o <= std_ulogic_vector(resize(unsigned(a_i) * unsigned(b_i), L_g));

	temp1_s <= unsigned(a_i(31 downto 16)) * unsigned(b_i(15 downto 0));
	temp2_s <= unsigned(a_i(15 downto 0)) * unsigned(b_i(31 downto 16));
	temp3_s <= unsigned(a_i(15 downto 0)) * unsigned(b_i(15 downto 0));

	temp4_s <= (temp3_reg(31 downto 16) + temp1_reg(15 downto 0)) & temp3_reg(15 downto 0);

	temp5_s <= (temp4_reg(31 downto 16) + temp2_1_reg(15 downto 0)) & temp4_reg(15 downto 0);

	p_o <= std_ulogic_vector(temp5_reg);

	process(clk_i)
	begin
		if (rising_edge(clk_i)) then
			if (rst_i = '1') then
				temp1_reg   <= (others => '0');
				temp2_0_reg <= (others => '0');
				temp2_1_reg <= (others => '0');
				temp3_reg   <= (others => '0');
				temp4_reg   <= (others => '0');
				temp5_reg   <= (others => '0');
			else
				temp1_reg   <= temp1_s;
				temp2_0_reg <= temp2_s;
				temp2_1_reg <= temp2_0_reg;
				temp3_reg   <= temp3_s;
				temp4_reg   <= temp4_s;
				temp5_reg   <= temp5_s;
			end if;
		end if;
	end process;

end rtl;
