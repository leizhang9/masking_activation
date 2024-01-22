library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.conversion_pkg.all;


entity expand is
  port (
    clk : in std_logic;
    rst : in std_logic;
    x   : in std_logic_vector(n_bit - 1 downto 0);
    r   : in std_logic_vector(n_bit - 1 downto 0);
    y   : out std_logic_vector(n_bit - 1 downto 0)
  );
end entity;

architecture behavioral of expand is

begin

  reg : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        y <= (others => '0');
      else
        y <= x xor r;
      end if;
    end if;
  end process;

end architecture;
