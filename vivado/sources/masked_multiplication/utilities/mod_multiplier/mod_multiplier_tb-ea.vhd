library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.mod_multiplier_32_pkg.all;

entity mod_multiplier_tb is
end mod_multiplier_tb;

architecture rtl of mod_multiplier_tb is
	constant clk_freq_c : positive := 100000000;
	constant L_c        : positive := 32; 

	signal clk_s        : std_ulogic := '0';
	signal rst_s        : std_ulogic;
	signal a_s          : std_ulogic_vector (L_c - 1 downto 0);
	signal b_s          : std_ulogic_vector (L_c - 1 downto 0);
	signal p_s          : std_ulogic_vector (L_c - 1 downto 0);



begin

	dut : mod_multiplier_32
	port map (
		a_i => a_s,
		b_i => b_s,
		p_o => p_s,
		clk_i => clk_s,
		rst_i => rst_s
	);

	clk_s <= not clk_s after ((1000000000/clk_freq_c)/2) * 1 ns;

	process 
	begin

		rst_s <= '0';

		wait until falling_edge(clk_s);
		report "Reset";
		rst_s <= '1';
		wait until falling_edge(clk_s);
		rst_s <= '0';

		a_s <= X"00000001";
		b_s <= X"00000002";
		wait until falling_edge(clk_s);
		wait for 1 ns;

		a_s <= X"00000000";
		b_s <= X"00000000";
		wait until falling_edge(clk_s);
		wait for 1 ns;

		a_s <= X"EFFFFFFF";
		b_s <= X"00000000";
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert p_s = X"00000002" severity error; -- pipelined, so this is the result for the first input

		a_s <= X"EFFFFFFF";
		b_s <= X"00000001";
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert p_s = X"00000000" severity error;

		a_s <= X"FFFFFFFF";
		b_s <= X"00000001";
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert p_s = X"00000000" severity error;

		a_s <= X"FFFFFFFF";
		b_s <= X"00000002";
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert p_s = X"EFFFFFFF" severity error;

		a_s <= X"FFFFFFFF";
		b_s <= X"FFFFFFFF";
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert p_s = X"FFFFFFFF" severity error;

		a_s <= X"80000000";
		b_s <= X"80000000";
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert p_s = X"FFFFFFFE" severity error;
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert p_s = X"00000001" severity error;
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert p_s = X"00000000" severity error;

		report "SIMULATION FINSIHED" severity failure;
		
	end process;

end rtl;