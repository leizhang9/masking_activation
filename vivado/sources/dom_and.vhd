-------------------------------------------------------------------------
-- Engineer: Matthias Probst
-- Create Date: 09.01.2023
-- Module Name: m_dom_and
-- Description: Domain Oriented Masked And for two domains 
--              two boolean shares (first order secure)
-------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity m_dom_and is
  port (
    clk     : in  std_logic;
    rst     : in  std_logic;
    en   : in  std_logic;

    -- inputs
    x      : in  std_logic_vector(1 downto 0);
    y      : in  std_logic_vector(1 downto 0);


    -- randomness
    r       : in  std_logic;

    -- outputs
    z      : out std_logic_vector(1 downto 0)
  );
end entity;

architecture behavioral of m_dom_and is
  attribute DONT_TOUCH : string;
  attribute keep : string;

  signal dom_a0b0  : std_logic;
  signal dom_a0b1  : std_logic;
  signal dom_a1b0  : std_logic;
  signal dom_a1b1  : std_logic;
  signal start_2   : std_logic;
  
  attribute keep of dom_a0b0 : signal is "true";
  attribute keep of dom_a0b1 : signal is "true";
  attribute keep of dom_a1b0 : signal is "true";
  attribute keep of dom_a1b1 : signal is "true";

begin


  -- reg stage
  reg_comb : process (clk) is
  begin
    if rising_edge(clk) then
      if en = '1' then
        dom_a0b0  <= x(0) and y(0);
        dom_a0b1  <= (x(0) and y(1)) xor r;
        dom_a1b0  <= (x(1) and y(0)) xor r;
        dom_a1b1  <= x(1) and y(1);
        start_2 <= '1';
      elsif rst = '1' then 
        dom_a0b0 <= '0';
        dom_a0b1 <= '0';
        dom_a1b0 <= '0';
        dom_a1b1 <= '0';
        start_2 <= '0';
      else 
        start_2 <= '0';
      end if;
    end if;
  end process reg_comb;

  -- out stage
  reg_out : process (clk) is
  begin
    if rising_edge(clk) then
      if start_2 = '1' then
        z(0)   <= dom_a0b0 xor dom_a0b1;
        z(1)   <= dom_a1b0 xor dom_a1b1;
      elsif rst = '1' then 
        z <= (others => '0');
      end if;
    end if;
  end process reg_out;

end architecture;
