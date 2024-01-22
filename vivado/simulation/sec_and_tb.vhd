library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;

entity sec_and_tb is
end entity;

architecture arch of sec_and_tb is

  component sec_and is
    port(
      clk : in std_logic;
      rst : in std_logic;
      en  : in std_logic;
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
  signal en : std_logic;
  signal z_comb : std_logic;
  signal x_comb : std_logic;
  signal y_comb : std_logic;

begin

  dut : sec_and port map (
    clk => clk,
    rst => rst,
    en => en,
    x => x,
    y => y,
    r => r,
    z => z
  );

  clk <= not clk after clk_period / 2;
  z_comb <= z(0) xor z(1);
  x_comb <= x(0) xor x(1);
  y_comb <= y(0) xor y(1);
  stim : process is
  begin
  en <= '1';
    rst <= '1';
    x <= "00";
    y <= "00";
    r <= '0';
    wait for 5*clk_period;
    rst <= '0';
    wait for 5*clk_period;
    x <= "10";
    y <= "01";
    r <= '1';
    wait for 5*clk_period;
    x <= "11";
    y <= "01";
    r <= '0';
    wait;
  end process;


end architecture;
