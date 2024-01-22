library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;

entity b2a_tcl_tb is
end b2a_tcl_tb;

architecture rtl of b2a_tcl_tb is
	constant clk_freq_c : positive := 100000000;
	constant L_c        : positive := 4;
	constant D_c        : positive := 2;

	signal clk_s        : std_logic := '0';
	signal rst_s        : std_logic;
	signal a_share_s    : std_logic_vector (L_c * D_c - 1 downto 0);
	signal b_share_s    : std_logic_vector (L_c * D_c - 1 downto 0);
	signal rnd_s        : std_logic_vector (L_c - 1 downto 0);
	signal gamma_s      : std_logic_vector (L_c - 1 downto 0);

	signal b0_s      : std_logic_vector (L_c - 1 downto 0);
	signal b1_s      : std_logic_vector (L_c - 1 downto 0);

	signal a_recomb_s : std_logic_vector (L_c - 1 downto 0);


	component boolean_to_arithmetic_sni is
		port (
			b_share_i      : in  std_logic_vector (L_c * D_c - 1 downto 0);
			rnd_i          : in  std_logic_vector (L_c * (D_c - 1) - 1 downto 0);
			gamma_i        : in  std_logic_vector (L_c * (D_c - 1) - 1 downto 0);
			clk_i          : in  std_logic;
			rst_i          : in  std_logic;
			a_share_o      : out std_logic_vector (L_c * D_c - 1 downto 0)
		);
	end component;

begin

	dut : boolean_to_arithmetic_sni port map (
		b_share_i => b_share_s,
		rnd_i => rnd_s,
		gamma_i => gamma_s,
		clk_i => clk_s,
		rst_i => rst_s,
		a_share_o => a_share_s
	);

	clk_s <= not clk_s after ((1000000000/clk_freq_c)/2) * 1 ns;

	b_share_s <= b0_s & b1_s;

	a_recomb_s <= std_logic_vector(unsigned(a_share_s((2 * L_c) - 1 downto L_c)) + unsigned(a_share_s(L_c - 1 downto 0)));

	process
	begin

		rst_s <= '0';
		wait until falling_edge(clk_s);
		report "Reset";
		rst_s <= '1';
		wait until falling_edge(clk_s);
		rst_s <= '0';

		rnd_s <= X"0";
		gamma_s <= X"0";

		b0_s <= X"0";
		b1_s <= X"0";

    wait;
	end process;

end rtl;
