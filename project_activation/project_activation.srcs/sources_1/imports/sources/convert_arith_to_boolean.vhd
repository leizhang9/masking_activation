library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.conversion_pkg.all;

entity convert_a_to_b is
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
end entity;

architecture behavioral of convert_a_to_b is

  component sec_add_universal is
    port (
      clk   : in std_logic;
      rst   : in std_logic;
      start : in std_logic;
      x     : in std_logic_vector(n_bit - 1 downto 0);
      y     : in std_logic_vector(n_bit - 1 downto 0);
      mx    : in std_logic_vector(n_bit - 1 downto 0);
      my    : in std_logic_vector(n_bit - 1 downto 0);
      r0    : in std_logic_vector(n_bit - 2 downto 0);
      r1    : in std_logic_vector(n_bit - 2 downto 0);
      r2    : in std_logic_vector(n_bit - 2 downto 0);
      done  : out std_logic;
      z0    : out std_logic_vector(n_bit - 1 downto 0);
      z1    : out std_logic_vector(n_bit - 1 downto 0)
    );
  end component;

  component expand is
    port (
      clk : in std_logic;
      rst : in std_logic;
      x   : in std_logic_vector(n_bit - 1 downto 0);
      r   : in std_logic_vector(n_bit - 1 downto 0);
      y   : out std_logic_vector(n_bit - 1 downto 0)
    );
  end component;

  signal x0 : std_logic_vector(n_bit - 1 downto 0);
  signal x1 : std_logic_vector(n_bit - 1 downto 0);
  signal y0 : std_logic_vector(n_bit - 1 downto 0);
  signal y1 : std_logic_vector(n_bit - 1 downto 0);
  signal start_int : std_logic;
  signal done_int : std_logic;


  attribute DONT_TOUCH : string;
  attribute keep : string;

  attribute keep of x0 : signal is "true";
  attribute keep of x1 : signal is "true";
  attribute keep of y0 : signal is "true";
  attribute keep of y1 : signal is "true";

  attribute DONT_TOUCH of sec_add_universal : component is "true";
  attribute DONT_TOUCH of expand : component is "true";


begin

  done <= done_int;
  start_int <= start;

  x1_expand : expand
  port map (
    clk => clk,
    rst => rst,
    x => A0,
    r => r0,
    y => x1
  );

  reg_x0 : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        x0 <= (others => '0');
      else
        x0 <= r0;
      end if;
    end if;
  end process;

  y1_expand : expand
  port map (
    clk => clk,
    rst => rst,
    x => A1,
    r => r1,
    y => y1
  );

  reg_y0 : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        y0 <= (others => '0');
      else
        y0 <= r1;
      end if;
    end if;
  end process;

  adder : sec_add_universal
  port map (
    clk => clk,
    rst => rst,
    start => start_int,
    x => x0,
    y => y0,
    mx => x1,
    my => y1,
    r0 => r2,
    r1 => r3,
    r2 => r4,
    done => done_int,
    z0 => z0,
    z1 => z1
  );

end architecture;
