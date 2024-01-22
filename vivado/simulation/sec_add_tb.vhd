library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity sec_add_tb is
end entity;

architecture arch of sec_add_tb is

  constant n_bit : integer := 32;
  constant clk_period : time := 10 ns;


  signal clk : std_logic := '0';
  signal rst : std_logic;
  signal start : std_logic;
  signal x : std_logic_vector(n_bit - 1 downto 0);
  signal mx : std_logic_vector(n_bit - 1 downto 0);
  signal y : std_logic_vector(n_bit - 1 downto 0);
  signal my : std_logic_vector(n_bit - 1 downto 0);
  signal r0 : std_logic_vector(n_bit - 2 downto 0);
  signal r1 : std_logic_vector(n_bit - 2 downto 0);
  signal r2 : std_logic_vector(n_bit - 2 downto 0);
  signal z0 : std_logic_vector(n_bit - 1 downto 0);
  signal z1 : std_logic_vector(n_bit - 1 downto 0);
  signal done : std_logic;
  
  signal result0 : std_logic_vector(n_bit - 1 downto 0);
  signal result1 : std_logic_vector(n_bit - 1 downto 0);
  

  component sec_add_universal is
    port(
      clk : in std_logic;
      rst : in std_logic;
      start : in std_logic;
      x  : in std_logic_vector(n_bit - 1 downto 0);
      mx  : in std_logic_vector(n_bit - 1 downto 0);
      y  : in std_logic_vector(n_bit - 1 downto 0);
      my  : in std_logic_vector(n_bit - 1 downto 0);
      r0  : in std_logic_vector(n_bit - 2 downto 0);
      r1  : in std_logic_vector(n_bit - 2 downto 0);
      r2  : in std_logic_vector(n_bit - 2 downto 0);
      z0  : out std_logic_vector(n_bit - 1 downto 0);
      z1  : out std_logic_vector(n_bit - 1 downto 0);
      done : out std_logic
    );
  end component;

begin

  dut : sec_add_universal
  port map (
    clk => clk,
    rst => rst,
    start => start,
    x => x,
    mx => mx,
    y => y,
    my => my,
    r0 => r0,
    r1 => r1,
    r2 => r2,
    z0 => z0,
    z1 => z1,
    done => done
  );

  clk <= not clk after clk_period / 2;
  result0 <= std_logic_vector(unsigned(x xor mx) + unsigned(y xor my));
  result1 <= std_logic_vector(unsigned(z0 xor z1));

  stim : process is
  begin
    rst <= '1';
    start <= '0';
    wait for 5*clk_period;
    rst <= '0';
    wait for 5*clk_period;
    x <= x"000000f7";
    mx <= x"00000018";
    y <= x"00000007";
    my <= x"00000002";
    r0 <= (others => '1');
    r1 <= (others => '1');
    r2 <= (others => '1');
    start <= '1';
    wait for clk_period;
    start <= '0';
    
    wait for 500*clk_period;
    x <= (others => '1');
    mx <= (others => '0');
    y <= x"000000ff";
    my <= (others => '1');
    r0 <= (others => '0');
    r1 <= (others => '1');
    r2 <= (others => '0');
    start <= '1';
    wait for clk_period;
    start <= '0';
    
    wait for 500*clk_period;
    x <= (others => '1');
    mx <= (others => '0');
    y <= (others => '0');
    my <= (others => '0');
    r0 <= (others => '1');
    r1 <= (others => '1');
    r2 <= (others => '1');
    start <= '1';
    wait for clk_period;
    start <= '0';
    
    wait for 500*clk_period;
    x <= (others => '1');
    mx <= (others => '1');
    y <= (others => '0');
    my <= (others => '1');
    r0 <= (others => '0');
    r1 <= (others => '0');
    r2 <= (others => '1');
    start <= '1';
    wait for clk_period;
    start <= '0';
    
    wait for 500*clk_period;
    x <= (others => '1');
    mx <= (others => '1');
    y <= (others => '0');
    my <= (others => '1');
    r0 <= (others => '1');
    r1 <= (others => '1');
    r2 <= (others => '1');
    start <= '1';
    wait for clk_period;
    start <= '0';
    
    wait;
  end process;

end architecture;
