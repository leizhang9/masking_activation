library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use work.conversion_pkg.all;

entity masked_cmp_trn_tb is
end entity;

architecture arch of masked_cmp_trn_tb is

  constant clk_period : time := 10ns;
  constant L_g        : positive := 32;
  constant D_g        : positive := 2;

  signal clk_i        : std_ulogic := '1';
	signal rst_i        : std_ulogic;
	signal a_i          : std_ulogic_vector (L_g * D_g - 1 downto 0);
	signal b_i          : std_ulogic_vector (L_g * D_g - 1 downto 0);
	signal rnd_i        : std_ulogic_vector (18 * L_g * (D_g - 1) - 1 downto 0);
  signal start_i      : std_logic;
	signal c_o          : std_ulogic_vector (L_g * D_g - 1 downto 0);
	signal d_o          : std_ulogic_vector (L_g * D_g - 1 downto 0);
	signal trn_o        : std_ulogic_vector (L_g * D_g - 1 downto 0);
  signal done_o       : std_ulogic;


begin

  clk_i <= not clk_i after clk_period / 2;

  dut : entity work.masked_cmp_trn
  generic map (
    L_g => L_g
  )
  port map (
    clk_i => clk_i,
    rst_i => rst_i,
    a_i => a_i,
    b_i => b_i,
    rnd_i => rnd_i,
    start_i => start_i,
    done_o => done_o,
    c_o => c_o,
    d_o => d_o,
    trn_o => trn_o
  );

  stim : process is
  begin
    rst_i <= '1';
    a_i <= (others => '0');
    b_i <= (others => '0');
    rnd_i <= (others => '0');
    start_i <= '0';
    wait for 5*clk_period;
    rst_i <= '0';
    wait for 5*clk_period;
    -- -10
    a_i <= x"0000000000001450";
    -- 40
    b_i <= x"00000000000000af";
    rnd_i <= x"112233445566778899aabbccddeeff00abcd112233445566778899aabbccddeeff00abcd112233445566778899aabbccddeeff00abcd112233445566778899aabbccddeeff00abcd";
    start_i <= '1';
    wait for clk_period;
    start_i <= '0';
    wait for 2700ns;
    -- 17
    a_i <= x"000000000000070a";
    -- 7
    b_i <= x"000000000000d532";
    --rnd_i <= x"112233445566778899aabbccdd6eff00abcd";
    start_i <= '1';
    wait for clk_period;
    start_i <= '0';
    wait for 2700ns;
    -- -10
    a_i <= x"0000000000009264";
    -- -10
    b_i <= x"000000000000ba3c";
    --rnd_i <= x"112233445566778899aa99ccddeeff00abcd";
    start_i <= '1';
    wait for clk_period;
    start_i <= '0';
    wait for 2700ns;
    -- 120
    a_i <= x"00000000000082f6";
    b_i <= x"0000000000000000";
    --rnd_i <= x"112233445566778899aa99ccddeeff00abcd";
    start_i <= '1';
    wait for clk_period;
    start_i <= '0';
    wait;
  end process;


end architecture;
