library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity sec_and is
  port (
    clk       : in std_logic;
    rst       : in std_logic;
    en        : in std_logic;
    x         : in std_logic_vector(1 downto 0);
    y         : in std_logic_vector(1 downto 0);
    r         : in std_logic;
    z         : out std_logic_vector(1 downto 0)
  );
end entity;

architecture behavioral of sec_and is

  signal inter_res5 : std_logic;
  signal inter_res1 : std_logic;
  signal inter_res2 : std_logic;
  signal inter_res3 : std_logic;
  signal inter_res4 : std_logic;
  signal z0         : std_logic;
  signal z1         : std_logic;

  attribute DONT_TOUCH : string;
  attribute keep : string;

  attribute keep of inter_res5  : signal is "true";
  attribute keep of inter_res1  : signal is "true";
  attribute keep of inter_res2  : signal is "true";
  attribute keep of inter_res3  : signal is "true";
  attribute keep of inter_res4  : signal is "true";
  attribute keep of z0          : signal is "true";
  attribute keep of z1          : signal is "true";

  attribute DONT_TOUCH of reg1  : label is "true";
  attribute DONT_TOUCH of reg2  : label is "true";
  attribute DONT_TOUCH of reg3  : label is "true";
  attribute DONT_TOUCH of reg4  : label is "true";
  attribute DONT_TOUCH of reg5  : label is "true";

begin
  z <= z0 & z1;
  
  reg1 : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        inter_res1 <= '0';
      elsif en = '1' then
        inter_res1 <= x(0) and y(0);
      end if;
    end if;
  end process;
  
  reg2 : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        z0 <= '0';
      elsif en = '1' then
        z0 <= inter_res1 xor r;
      end if;
    end if;
  end process;
  
  reg3 : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        inter_res2 <= '0';
      elsif en = '1' then
        inter_res2 <= x(0) and y(1);
      end if;
    end if;
  end process;
  
  reg4 : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        inter_res3 <= '0';
      elsif en = '1' then
        inter_res3 <= x(1) and y(0);
      end if;
    end if;
  end process;
  
  reg5 : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        inter_res4 <= '0';
      elsif en = '1' then
        inter_res4 <= x(1) and y(1);
      end if;
    end if;
  end process;
  
  reg6 : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        inter_res5 <= '0';
      elsif en = '1' then
        inter_res5 <= (inter_res2 xor r) xor (inter_res3);
      end if;
    end if;
  end process;
  
  reg7 : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        z1 <= '0';
      elsif en = '1' then
        z1 <= inter_res5 xor inter_res4;
      end if;
    end if;
  end process;

end architecture;
