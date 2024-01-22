library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;

entity sec_and_tcl_tb is
end entity;

architecture arch of sec_and_tcl_tb is

  component sec_and is
    port(
      clk : in std_logic;
      rst : in std_logic;
      x   : in std_logic_vector(1 downto 0);
      y   : in std_logic_vector(1 downto 0);
      r   : in std_logic;
      z   : out std_logic_vector(1 downto 0)
    );
  end component;

  constant clk_period : time := 10 ns;

  signal clk : std_logic := '1';
  signal rst : std_logic;
  signal x : std_logic_vector(1 downto 0);
  signal y : std_logic_vector(1 downto 0);
  signal r : std_logic;
  signal z : std_logic_vector(1 downto 0);

begin

  dut : sec_and port map (
    clk => clk,
    rst => rst,
    x => x,
    y => y,
    r => r,
    z => z
  );

  clk <= not clk after clk_period / 2;

  stim : process is
  begin
    rst <= '1';
    wait for 2*clk_period;
    rst <= '0';
    wait for 2*clk_period;
    x <= "00";
    y <= "00";
    r <= '0';
    wait;
  end process;


end architecture;
