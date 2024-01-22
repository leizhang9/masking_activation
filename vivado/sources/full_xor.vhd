library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.conversion_pkg.all;

entity full_xor is
  port (
    clk : in std_logic;
    rst : in std_logic;
    en : in std_logic;
    x0 : in std_logic_vector(n_bit - 1 downto 0);
    x1 : in std_logic_vector(n_bit - 1 downto 0);
    r : in std_logic_vector(n_bit - 1 downto 0);
    z : out std_logic_vector(n_bit - 1 downto 0)
  );
end entity;

architecture behaviroal of full_xor is

  component refresh_masks is
    port (
      clk : in std_logic;
      rst : in std_logic;
      x0 : in std_logic_vector(n_bit - 1 downto 0);
      x1 : in std_logic_vector(n_bit - 1 downto 0);
      r : in std_logic_vector(n_bit - 1 downto 0);
      z0 : out std_logic_vector(n_bit - 1 downto 0);
      z1 : out std_logic_vector(n_bit - 1 downto 0)
    );
  end component;

  signal y0 : std_logic_vector(n_bit - 1 downto 0);
  signal y1 : std_logic_vector(n_bit - 1 downto 0);
  signal r_int : std_logic_vector(n_bit - 1 downto 0);
  signal x0_int : std_logic_vector(n_bit - 1 downto 0);
  signal x1_int : std_logic_vector(n_bit - 1 downto 0);

  attribute DONT_TOUCH : string;
  attribute keep : string;

  attribute DONT_TOUCH of refresh_masks : component is "true";

  attribute keep of x0_int : signal is "true";
  attribute keep of x1_int : signal is "true";
  attribute keep of y1 : signal is "true";
  attribute keep of y0 : signal is "true";
  attribute keep of r_int : signal is "true";

begin

  reg : process(clk)
  begin
      if clk'event and clk = '1' then
        if rst = '1' then
          x0_int <= (others => '0');
          x1_int <= (others => '0');
          r_int <= (others => '0');
        elsif en = '1' then
          x0_int <= x0;
          x1_int <= x1;
          r_int <= r;
        end if;
      end if;
  end process;

  refresh : refresh_masks
  port map (
    clk => clk,
    rst => rst,
    x0 => x0_int,
    x1 => x1_int,
    r => r_int,
    z0 => y0,
    z1 => y1
  );

  f_xor : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        z <= (others => '0');
      elsif en = '1' then
        z <= y0 xor y1;
      end if;
    end if;
  end process;

end architecture;
