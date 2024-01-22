library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity convert_a_to_b_tb is
end entity;

architecture arch of convert_a_to_b_tb is

  constant n_bit : integer := 8;
  constant clk_period : time := 10 ns;


  signal clk : std_logic := '0';
  signal rst : std_logic;
  signal start : std_logic;
  signal A0 : std_logic_vector(n_bit - 1 downto 0);
  signal A1 : std_logic_vector(n_bit - 1 downto 0);
  signal r0 : std_logic_vector(n_bit - 1 downto 0);
  signal r1 : std_logic_vector(n_bit - 1 downto 0);
  signal r2 : std_logic_vector(n_bit - 2 downto 0);
  signal r3 : std_logic_vector(n_bit - 2 downto 0);
  signal r4 : std_logic_vector(n_bit - 2 downto 0);
  signal done : std_logic;
  signal z0 : std_logic_vector(n_bit - 1 downto 0);
  signal z1 : std_logic_vector(n_bit - 1 downto 0);

  component convert_a_to_b is
    port (
      clk   : in std_logic;
      rst   : in std_logic;
      start : in std_logic;
      A0    : in std_logic_vector(n_bit - 1 downto 0);
      A1    : in std_logic_vector(n_bit - 1 downto 0);
      r0    : in std_logic_vector(n_bit - 1 downto 0);
      r1    : in std_logic_vector(n_bit - 1 downto 0);
      r2    : in std_logic_vector(n_bit - 2 downto 0);
      r3    : in std_logic_vector(n_bit - 2 downto 0);
      r4    : in std_logic_vector(n_bit - 2 downto 0);
      done  : out std_logic;
      z0    : out std_logic_vector(n_bit - 1 downto 0);
      z1    : out std_logic_vector(n_bit - 1 downto 0)
    );
  end component;

begin

  dut : convert_a_to_b
  port map (
    clk => clk,
    rst => rst,
    start => start,
    A0 => A0,
    A1 => A1,
    r0 => r0,
    r1 => r1,
    r2 => r2,
    r3 => r3,
    r4 => r4,
    done => done,
    z0 => z0,
    z1 => z1
  );

  clk <= not clk after clk_period / 2;

  stim : process is
  begin
    rst <= '1';
    start <= '0';
    wait for 5*clk_period;
    rst <= '0';
    wait for 5*clk_period;
    A0 <= x"f7";
    r0 <= (others => '0');
    A1 <= x"00";
    r1 <= (others => '1');
    r2 <= (others => '1');
    r3 <= (others => '1');
    r4 <= (others => '1');
    wait for clk_period;
    start <= '1';
    wait for clk_period;
    start <= '0';

    wait for 50*clk_period;
    A0 <= (others => '1');
    r0 <= (others => '0');
    A1 <= x"ff";
    r1 <= (others => '1');
    r2 <= (others => '0');
    r3 <= (others => '1');
    r4 <= (others => '0');
    wait for clk_period;
    start <= '1';
    wait for clk_period;
    start <= '0';

    wait for 50*clk_period;
    A0 <= (others => '1');
    r0 <= (others => '0');
    A1 <= (others => '0');
    r1 <= (others => '0');
    r2 <= (others => '1');
    r3 <= (others => '1');
    r4 <= (others => '1');
    wait for clk_period;
    start <= '1';
    wait for clk_period;
    start <= '0';

    wait for 50*clk_period;
    A0 <= (others => '1');
    r0 <= (others => '1');
    A1 <= (others => '0');
    r1 <= (others => '1');
    r2 <= (others => '0');
    r3 <= (others => '0');
    r4 <= (others => '1');
    wait for clk_period;
    start <= '1';
    wait for clk_period;
    start <= '0';

    wait for 50*clk_period;
    A0 <= (others => '1');
    r0 <= (others => '1');
    A1 <= (others => '0');
    r1 <= (others => '1');
    r2 <= (others => '1');
    r3 <= (others => '1');
    r4 <= (others => '1');
    wait for clk_period;
    start <= '1';
    wait for clk_period;
    start <= '0';

    wait;
  end process;

end architecture;
