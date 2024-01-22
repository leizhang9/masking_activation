library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.conversion_pkg.all;

entity convert_b_to_a is
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
end entity;

architecture behavioral of convert_b_to_a is

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

  component full_xor
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

  signal modul : std_logic_vector(n_bit downto 0) := '1' & (n_bit - 1 downto 0 => '0');

  signal A0_int : std_logic_vector(n_bit - 1 downto 0);
  signal A1_int : std_logic_vector(n_bit - 1 downto 0);
  signal A0d : std_logic_vector(n_bit - 1 downto 0);
  signal A1d : std_logic_vector(n_bit - 1 downto 0) := (others => '0');
  signal c_done : std_logic;
  signal y0 : std_logic_vector(n_bit - 1 downto 0);
  signal y1 : std_logic_vector(n_bit - 1 downto 0);

  signal a_done : std_logic;
  signal z0 : std_logic_vector(n_bit - 1 downto 0);
  signal z1 : std_logic_vector(n_bit - 1 downto 0);
  signal delay_done : std_logic_vector(2 downto 0);
  signal done_int : std_logic;

  signal en_xor : std_logic;

  attribute DONT_TOUCH : string;
  attribute keep : string;

  attribute DONT_TOUCH of sec_add_universal : component is "true";
  attribute DONT_TOUCH of convert_a_to_b : component is "true";
  attribute DONT_TOUCH of full_xor : component is "true";

  attribute keep of A0_int : signal is "true";
  attribute keep of A1_int : signal is "true";
  attribute keep of A0d : signal is "true";
  attribute keep of A1d : signal is "true";
  attribute keep of c_done : signal is "true";
  attribute keep of y0 : signal is "true";
  attribute keep of y1 : signal is "true";
  attribute keep of a_done : signal is "true";
  attribute keep of z0 : signal is "true";
  attribute keep of z1 : signal is "true";

begin

  A0 <= A0_int;
  A1 <= A1_int;
  done <= done_int;

  en_xor <= delay_done(0) or delay_done(1) or delay_done(2);

  A0_int <= r0;
  A0d <= std_logic_vector(resize((unsigned(modul) - unsigned(r0)), n_bit));

  reg : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        delay_done <= (others => '0');
        done_int <= '0';
      else
        delay_done <= std_logic_vector(shift_left(unsigned(delay_done), 1));
        delay_done(0) <= a_done;
        done_int <= delay_done(2);
      end if;
    end if;
  end process;

  conv : convert_a_to_b
  port map (
    clk => clk,
    rst => rst,
    start => start,
    A0 => A0d,
    A1 => A1d,
    r0 => c_r0,
    r1 => c_r1,
    r2 => c_r2,
    r3 => c_r3,
    r4 => c_r4,
    done => c_done,
    z0 => y0,
    z1 => y1
  );

  add : sec_add_universal
  port map (
    clk => clk,
    rst => rst,
    start => c_done,
    x => x0,
    y => y0,
    mx => x1,
    my => y1,
    r0 => a_r0,
    r1 => a_r1,
    r2 => a_r2,
    done => a_done,
    z0 => z0,
    z1 => z1
  );

  f_x : full_xor
  port map(
    clk => clk,
    rst => rst,
    en => en_xor,
    x0 => z0,
    x1 => z1,
    r => x_r,
    z => A1_int
  );


end architecture;
