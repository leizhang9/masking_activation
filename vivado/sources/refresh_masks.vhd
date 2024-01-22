library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.conversion_pkg.all;

entity refresh_masks is
  port (
    clk : in std_logic;
    rst : in std_logic;
    x0 : in std_logic_vector(n_bit - 1 downto 0);
    x1 : in std_logic_vector(n_bit - 1 downto 0);
    r : in std_logic_vector(n_bit - 1 downto 0);
    z0 : out std_logic_vector(n_bit - 1 downto 0);
    z1 : out std_logic_vector(n_bit - 1 downto 0)
  );
end entity;

architecture behaviroal of refresh_masks is

  signal z0_int : std_logic_vector(n_bit - 1 downto 0);
  signal z1_int : std_logic_vector(n_bit - 1 downto 0);

begin

  z0 <= z0_int;
  z1 <= z1_int;

  refresh : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        z0_int <= (others => '0');
        z1_int <= (others => '0');
      else
        z0_int <= x0 xor r;
        z1_int <= x1 xor r;
      end if;
    end if;
  end process;


end architecture;
