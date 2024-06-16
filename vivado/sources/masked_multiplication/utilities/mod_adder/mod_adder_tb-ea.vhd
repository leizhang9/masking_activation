library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.mod_adder_pkg.all;

entity mod_adder_tb is
end mod_adder_tb;

architecture rtl of mod_adder_tb is
	constant clk_freq_c : positive := 100000000;
	constant L_c        : positive := 32; 

	signal clk_s        : std_ulogic := '0';
	signal a_s          : std_ulogic_vector (L_c - 1 downto 0);
	signal b_s          : std_ulogic_vector (L_c - 1 downto 0);
	signal s_s          : std_ulogic_vector (L_c - 1 downto 0);

begin

	dut : mod_adder generic map (
		L_g => L_c
	) port map (
		a_i => a_s,
		b_i => b_s,
		s_o => s_s
	);

	clk_s <= not clk_s after ((1000000000/clk_freq_c)/2) * 1 ns;

	process 
	begin
		a_s <= X"00000000";
		b_s <= X"00000000";
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert s_s = X"00000000" severity error;

		a_s <= X"EFFFFFFF";
		b_s <= X"00000000";
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert s_s = X"EFFFFFFF" severity error;

		a_s <= X"EFFFFFFF";
		b_s <= X"00000001";
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert s_s = X"F0000000" severity error;

		a_s <= X"FFFFFFFF";
		b_s <= X"00000001";
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert s_s = X"00000000" severity error;

		a_s <= X"FFFFFFFF";
		b_s <= X"FFFFFFFF";
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert s_s = X"FFFFFFFE" severity error;

		a_s <= X"80000000";
		b_s <= X"80000000";
		wait until falling_edge(clk_s);
		wait for 1 ns;
		assert s_s = X"00000000" severity error;

		report "SIMULATION FINSIHED" severity failure;
		
	end process;

end rtl;