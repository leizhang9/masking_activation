library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.my_package.all;

entity random_generator is
    port (
        clk     : in  std_logic;
        reset   : in  std_logic;
        rnd_out : out std_logic_vector(K-1 downto 0)
    );
end entity;

architecture Behavioral of random_generator is
    signal lfsr : std_logic_vector(K-1 downto 0); 
    signal temp_rnd : integer range 0 to prime-1;     -- Temporary variable for the random number in the range 0-6
begin
    process(clk, reset)
    begin
        if reset = '1' then
            lfsr <= "00000001"; -- Non-zero initialization
        elsif rising_edge(clk) then
            -- Example LFSR update logic
            lfsr <= lfsr(6 downto 0) & (lfsr(7) xor lfsr(5) xor lfsr(4) xor lfsr(3));
        end if;
    end process;

    -- Map the 8-bit number to the range 0-6
    temp_rnd <= to_integer(unsigned(lfsr)) mod prime;

    -- Convert integer to std_logic_vector
    rnd_out <= std_logic_vector(to_unsigned(temp_rnd, K));

end architecture;
