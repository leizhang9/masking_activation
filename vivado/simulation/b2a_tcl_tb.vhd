library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity b2a_tcl_tb is
end entity;

architecture arch of b2a_tcl_tb is

  constant n_bit : integer := 8;
  constant clk_period : time := 10 ns;

  signal clk : std_logic := '0';
  signal rst : std_logic;
  signal start : std_logic;
  signal x0    : std_logic_vector(n_bit - 1 downto 0);
  signal x1    : std_logic_vector(n_bit - 1 downto 0);
  signal r0    : std_logic_vector(n_bit - 1 downto 0);
  signal c_r0  : std_logic_vector(n_bit - 1 downto 0);
  signal c_r1  : std_logic_vector(n_bit - 1 downto 0);
  signal c_r2  : std_logic_vector(n_bit - 2 downto 0);
  signal c_r3  : std_logic_vector(n_bit - 2 downto 0);
  signal c_r4  : std_logic_vector(n_bit - 2 downto 0);
  signal a_r0  : std_logic_vector(n_bit - 2 downto 0);
  signal a_r1  : std_logic_vector(n_bit - 2 downto 0);
  signal a_r2  : std_logic_vector(n_bit - 2 downto 0);
  signal x_r   : std_logic_vector(n_bit - 1 downto 0);
  signal done  : std_logic;
  signal A0    : std_logic_vector(n_bit - 1 downto 0);
  signal A1    : std_logic_vector(n_bit - 1 downto 0);

  component convert_b_to_a is
    port (
      clk   : in std_logic;
      rst   : in std_logic;
      start : in std_logic;
      x0    : in std_logic_vector(n_bit - 1 downto 0);
      x1    : in std_logic_vector(n_bit - 1 downto 0);
      r0    : in std_logic_vector(n_bit - 1 downto 0);
      c_r0  : in std_logic_vector(n_bit - 1 downto 0);
      c_r1  : in std_logic_vector(n_bit - 1 downto 0);
      c_r2  : in std_logic_vector(n_bit - 2 downto 0);
      c_r3  : in std_logic_vector(n_bit - 2 downto 0);
      c_r4  : in std_logic_vector(n_bit - 2 downto 0);
      a_r0  : in std_logic_vector(n_bit - 2 downto 0);
      a_r1  : in std_logic_vector(n_bit - 2 downto 0);
      a_r2  : in std_logic_vector(n_bit - 2 downto 0);
      x_r   : in std_logic_vector(n_bit - 1 downto 0);
      done  : out std_logic;
      A0    : out std_logic_vector(n_bit - 1 downto 0);
      A1    : out std_logic_vector(n_bit - 1 downto 0)
    );
  end component;

begin

  dut : convert_b_to_a
  port map (
    clk => clk,
    rst => rst,
    start => start,
    x0 => x0,
    x1 => x1,
    r0 => r0,
    c_r0 => c_r0,
    c_r1 => c_r1,
    c_r2 => c_r2,
    c_r3 => c_r3,
    c_r4 => c_r4,
    a_r0 => a_r0,
    a_r1 => a_r1,
    a_r2 => a_r2,
    x_r => x_r,
    done => done,
    A0 => A0,
    A1 => A1
  );

  clk <= not clk after clk_period / 2;

  stim : process is
  begin
    rst <= '1';
    start <= '0';
    x0 <= x"00";
    r0 <= (others => '0');
    x1 <= x"00";
    c_r0 <= (others => '0');
    c_r1 <= (others => '0');
    c_r2 <= (others => '0');
    c_r3 <= (others => '0');
    c_r4 <= (others => '0');
    a_r0 <= (others => '0');
    a_r1 <= (others => '0');
    a_r2 <= (others => '0');
    x_r <= (others => '0');
    wait for 5*clk_period;
    rst <= '0';

    wait;
  end process;

end architecture;
