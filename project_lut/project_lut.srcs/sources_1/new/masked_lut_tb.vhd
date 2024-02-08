----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 2024/01/20 00:34:57
-- Design Name: 
-- Module Name: masked_lut_tb - Behavioral
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
use IEEE.STD_LOGIC_1164.ALL;
use work.my_package.all;
-- Uncomment the following library declaration if using
-- arithmetic functions with Signed or Unsigned values
--use IEEE.NUMERIC_STD.ALL;

-- Uncomment the following library declaration if instantiating
-- any Xilinx leaf cells in this code.
--library UNISIM;
--use UNISIM.VComponents.all;

entity masked_lut_tb is
--  Port ( );
end masked_lut_tb;

architecture Behavioral of masked_lut_tb is

    component masked_lut 
    port(
        x: in std_logic_vector(K-1 downto 0); --x
        clk: in std_logic;
        reset: in std_logic;
        output: out std_logic_vector(K-1 downto 0);
        rnd: in std_logic_vector(K-1 downto 0));  --for tcl
    end component;
    
    --Inputs
    signal x: std_logic_vector(K-1 downto 0) := "00000000";
    signal clk   : std_logic := '0';
    signal reset : std_logic := '1';
    signal rnd : std_logic_vector(K-1 downto 0);  --for tcl
    --Outputs
    signal output : std_logic_vector(K-1 downto 0);

    -- Clock period definitions
    constant clk_period : time := 10 ns;
begin
    dut: masked_lut port map (
        x => x,
        clk => clk,
        reset => reset,
        output => output,
        rnd => rnd   --for tcl
    );
    -- Clock process definitions
    clk_process :process
    begin
        clk <= '0';
        wait for clk_period/2;
        clk <= '1';
        wait for clk_period/2;
    end process;
    
--    x_process: process
--    begin
--        wait for clk_period*10;
--        x <= "00000001";
--        wait for clk_period*10;
--        x <= "00000010";
--        wait for clk_period*10;
--        x <= "00000011";
--        wait for clk_period*10;
--        x <= "00000100";
--        wait for clk_period*10;
--        x <= "00000101";
--        wait for clk_period*10;
--        x <= "00000110";
--    end process;
    
--    rnd_process: process
--    begin
--        wait for clk_period;
--        rnd <= "00000001";
--        wait for clk_period*10;
--        rnd <= "00000010";
--        wait for clk_period*10;
--        wait;
--    end process;

    -- Stimulus process
    stim_proc: process
    begin       
        -- Apply reset
        reset <= '1';
        wait for 20 ns;  
        reset <= '0';
        -- Let it run for some cycles
--        wait for 1000 ns;

        -- Complete the simulation
        wait;
    end process;

end Behavioral;
