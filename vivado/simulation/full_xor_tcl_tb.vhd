library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity full_xor_tcl_tb is
end entity;

architecture arch of full_xor_tcl_tb is

  constant n_bit : integer := 8;
  constant clk_period : time := 10 ns;

  signal clk : std_logic := '0';
  signal rst : std_logic;
  signal en : std_logic;
  signal x0 : std_logic_vector(n_bit - 1 downto 0);
  signal x1 : std_logic_vector(n_bit - 1 downto 0);
  signal r : std_logic_vector(n_bit - 1 downto 0);
  signal z : std_logic_vector(n_bit - 1 downto 0);

  component full_xor is
    port (
      clk : in std_logic;
      rst : in std_logic;
      en : in std_logic;
      x0 : in std_logic_vector(n_bit - 1 downto 0);
      x1 : in std_logic_vector(n_bit - 1 downto 0);
      r : in std_logic_vector(n_bit - 1 downto 0);
      z : out std_logic_vector(n_bit - 1 downto 0)
    );
  end component;

begin

  clk <= not clk after clk_period / 2;

  dut : full_xor
  port map (
    clk => clk,
    rst => rst,
    x0 => x0,
    x1 => x1,
    r => r,
    z => z
  );

  stim : process
  begin
    rst <= '1';
    en <= '1';
    x0 <= (others => '0');
    x1 <= (others => '0');
    r <= (others => '0');
    wait for 5*clk_period;
    rst <= '0';
    wait;
  end process;


end architecture;
