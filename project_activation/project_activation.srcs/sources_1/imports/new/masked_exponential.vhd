----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 03/18/2024 09:49:28 AM
-- Design Name: 
-- Module Name: masked_exponential - Behavioral
-- Project Name: 
-- Target Devices: 
-- Tool Versions: 
-- Description: 
-- 
-- Dependencies: 
-- 
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
-- 
----------------------------------------------------------------------------------
library IEEE;
library ieee_proposed;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.all;
use IEEE.std_logic_unsigned.all;

use ieee_proposed.fixed_float_types.all;
use ieee_proposed.fixed_pkg.all;
use ieee_proposed.float_pkg.all;
use work.my_package.all;

--entity masked_exponential is
--    Port (
--        x : in sfixed(15 downto -16); -- Input x in Q15.16 format
--        reset: in std_logic;
--        rnd: in std_logic_vector(K-1 downto 0);
--        e_x : out sfixed(31 downto -32)
--    );
--end masked_exponential;
entity masked_exponential is
    port(
        x1: in std_logic_vector(K-1 downto 0); --x1
        clk: in std_logic;
        reset: in std_logic;
        rnd: in std_logic_vector(K-1 downto 0);
        r0: in std_logic_vector(K-1 downto 0);
        r1: in std_logic_vector(K-1 downto 0);
        r2: in std_logic_vector(K-1 downto 0);
        done_o: out std_logic;
        output: out std_logic_vector(2*K-1 downto 0));
end masked_exponential;

architecture Behavioral of masked_exponential is
    -- Constants for the computation
    constant ln2 : sfixed(K-fractional_bits -1 downto -fractional_bits) := to_sfixed(0.69314718, K-fractional_bits -1, -fractional_bits); 
    constant log2e : sfixed(K-fractional_bits -1 downto -fractional_bits) := to_sfixed(1.44269504, K-fractional_bits -1, -fractional_bits); -- log2(e) approximation
    
    signal x0_sfixed: sfixed(K-fractional_bits -1 downto -fractional_bits);
    signal x1_sfixed: sfixed(K-fractional_bits -1 downto -fractional_bits);
    signal r0_sfixed: sfixed(K-fractional_bits -1 downto -fractional_bits);
    signal r1_sfixed: sfixed(K-fractional_bits -1 downto -fractional_bits);
    signal r2_sfixed: sfixed(K-fractional_bits -1 downto -fractional_bits);
    signal output_sfixed: sfixed(K-fractional_bits -1 downto -fractional_bits) := to_sfixed(0, K-fractional_bits -1, -fractional_bits);
    
    signal t0, t1 : sfixed(K-fractional_bits -1 downto -fractional_bits);
    signal m0, m1 : integer;
    signal two_power_m0, two_power_m1 : sfixed(K-fractional_bits -1 downto -fractional_bits);
    signal n0, n1 : sfixed(K-fractional_bits -1 downto -fractional_bits);
    signal k0_sfixed, k1_sfixed, e_k0, e_k1 : sfixed(K-fractional_bits -1 downto -fractional_bits); 
    
    signal xm0, xm1, ym0, ym1, z0, z1 : sfixed(K-fractional_bits -1 downto -fractional_bits):= (others => '0');
    signal xm0ym0_reg : sfixed(K-fractional_bits -1 downto -fractional_bits):= (others => '0');
    signal xm1ym1_reg : sfixed(K-fractional_bits -1 downto -fractional_bits):= (others => '0');
    signal xm0ym1_reg : sfixed(K-fractional_bits -1 downto -fractional_bits):= (others => '0');
    signal xm1ym0_reg : sfixed(K-fractional_bits -1 downto -fractional_bits):= (others => '0');
    signal count_reg : std_logic_vector(2 downto 0) := (others => '0');
    
    attribute keep: string;
    attribute keep of rnd: signal is "true";
    attribute keep of r0: signal is "true";
    attribute keep of r1: signal is "true";
    attribute keep of r2: signal is "true";
    attribute keep of r0_sfixed: signal is "true";
    attribute keep of r1_sfixed: signal is "true";
    attribute keep of r2_sfixed: signal is "true";
    
    attribute keep of x0_sfixed: signal is "true";
    attribute keep of x1: signal is "true";
    attribute keep of x1_sfixed: signal is "true";
    attribute keep of t0: signal is "true";
    attribute keep of t1: signal is "true";
    attribute keep of m0: signal is "true";
    attribute keep of m1: signal is "true";
    attribute keep of n0: signal is "true";
    attribute keep of n1: signal is "true";
    attribute keep of xm0: signal is "true";
    attribute keep of ym0: signal is "true";
    attribute keep of xm0ym0_reg: signal is "true";
    attribute keep of xm1ym1_reg: signal is "true";
    attribute keep of xm0ym1_reg: signal is "true";
    attribute keep of xm1ym0_reg: signal is "true";
    
begin
    x0_sfixed <= to_sfixed(signed(rnd), K-1, 0);  --to keep data unchanged
    x1_sfixed <= to_sfixed(signed(x1), K-1, 0);
    r0_sfixed <= to_sfixed(signed(r0), K-1, 0);
    r1_sfixed <= to_sfixed(signed(r1), K-1, 0);
    r2_sfixed <= to_sfixed(signed(r2), K-1, 0);
    -- Calculate t = x * log2(e)
    t0 <= resize(x0_sfixed * log2e, t0'high, t0'low);
    t1 <= resize(x1_sfixed * log2e, t1'high, t1'low);
    -- Split t into integer part (m) and fractional part (n)
    m0 <= to_integer(t0);
    m1 <= to_integer(t1);
    n0 <= resize((t0 - to_sfixed(m0, t0'high, t0'low)), n0'high, n0'low);
    n1 <= resize((t1 - to_sfixed(m1, t1'high, t1'low)), n1'high, n1'low);
    
    k0_sfixed <= resize(n0 * ln2, k0_sfixed'high, k0_sfixed'low);
    k1_sfixed <= resize(n1 * ln2, k1_sfixed'high, k1_sfixed'low);
    -- number of terms: 3
--    e_k0 <= resize((to_sfixed(1, e_k0'high, e_k0'low) + resize(k0_sfixed, e_k0'high, e_k0'low) + resize((k0_sfixed*k0_sfixed)/2, e_k0'high, e_k0'low)), e_k0'high, e_k0'low);
--    e_k1 <= resize((to_sfixed(1, e_k1'high, e_k1'low) + resize(k1_sfixed, e_k1'high, e_k1'low) + resize((k1_sfixed*k1_sfixed)/2, e_k1'high, e_k1'low)), e_k1'high, e_k1'low);
    -- number of terms: 5
    e_k0 <= resize((to_sfixed(1, e_k0'high, e_k0'low) + resize(k0_sfixed, e_k0'high, e_k0'low) + resize((k0_sfixed*k0_sfixed)/2, e_k0'high, e_k0'low) + resize((k0_sfixed*k0_sfixed*k0_sfixed)/6, e_k0'high, e_k0'low) + resize((k0_sfixed*k0_sfixed*k0_sfixed*k0_sfixed)/24, e_k0'high, e_k0'low)), e_k0'high, e_k0'low);
    e_k1 <= resize((to_sfixed(1, e_k1'high, e_k1'low) + resize(k1_sfixed, e_k1'high, e_k1'low) + resize((k1_sfixed*k1_sfixed)/2, e_k1'high, e_k1'low) + resize((k1_sfixed*k1_sfixed*k1_sfixed)/6, e_k1'high, e_k1'low) + resize((k1_sfixed*k1_sfixed*k1_sfixed*k1_sfixed)/24, e_k1'high, e_k1'low)), e_k1'high, e_k1'low);
    
    two_power_m0 <= SHIFT_LEFT(to_sfixed(2.0, K-fractional_bits -1, -fractional_bits), m0-1);
    two_power_m1 <= SHIFT_LEFT(to_sfixed(2.0, K-fractional_bits -1, -fractional_bits), m1-1);
    
    xm0 <= resize(two_power_m0 * e_k0 - r0_sfixed, xm0'high, xm0'low); --use r0
    xm1 <= r0_sfixed;
    ym0 <= resize(two_power_m1 * e_k1 - r1_sfixed, ym0'high, ym0'low); --use r1
    ym1 <= r1_sfixed;
    
    reg_after_xm0ym0:process(clk) is
    begin
        if clk'event and clk='1' then
            if reset='1' then
                xm0ym0_reg <= (others => '0');
            else
                xm0ym0_reg <= resize(xm0*ym0 - r2_sfixed, xm0ym0_reg'high, xm0ym0_reg'low);
            end if;
        end if;
    end process;
    
    reg_after_xm1ym1:process(clk) is
    begin
        if clk'event and clk='1' then
            if reset='1' then
                xm1ym1_reg <= (others => '0');
            else
                xm1ym1_reg <= resize(xm1*ym1, xm1ym1_reg'high, xm1ym1_reg'low);
            end if;
        end if;
    end process;
    
    reg_after_xm0ym1:process(clk) is
    begin
        if clk'event and clk='1' then
            if reset='1' then
                xm0ym1_reg <= (others => '0');
            else
                xm0ym1_reg <= resize(xm0*ym1 + r2_sfixed, xm0ym1_reg'high, xm0ym1_reg'low);
            end if;
        end if;
    end process;
    
    reg_after_xm1ym0:process(clk) is
    begin
        if clk'event and clk='1' then
            if reset='1' then
                xm1ym0_reg <= (others => '0');
            else
                xm1ym0_reg <= resize(xm1*ym0, xm1ym0_reg'high, xm1ym0_reg'low);
            end if;
        end if;
    end process;
    
    process(clk) is
    begin
        if clk'event and clk='1' then
            if reset='1' then
                z0 <= (others=>'0');
                z1 <= (others=>'0');
            else
                z0 <= resize(xm0ym0_reg + xm1ym1_reg, z0'high, z0'low);
                z1 <= resize(xm0ym1_reg + xm1ym0_reg, z0'high, z0'low);
            end if;
        end if;
    end process;
    
    counter: process(clk, reset)
    begin
        if clk'event and clk='1' then
            if reset = '1' then
                count_reg <= (others => '0');
            else
                if count_reg = "111" then
                    count_reg <= (others => '0');
                else 
                    count_reg <= count_reg + 1;
                end if;
            end if;
        end if;
    end process;
    
    done_o_assignment: process(count_reg)
    begin
        if count_reg = "111" then
            done_o <= '1';
        else
            done_o <= '0';
        end if;
    end process;

--    output_sfixed <= resize(z0 + z1, output_sfixed'high, output_sfixed'low);
--    output <= to_slv(output_sfixed);
    --masked output
    output <= to_slv(z1) & to_slv(z0);
end Behavioral;